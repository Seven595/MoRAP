"""Regression checks for reading artifacts created before the MoRAP rename."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from morap import model
from morap.compat import artifact_path, artifact_value, compatible_environment
from morap.paths import environment_value


class CompatibilityTests(unittest.TestCase):
    def test_current_environment_overrides_legacy_and_preserves_empty_value(self):
        with patch.dict(os.environ, {"LIN_MNP_CACHE_ROOT": "old-cache"}, clear=True):
            self.assertEqual(environment_value("MORAP_CACHE_ROOT"), "old-cache")
            os.environ["MORAP_CACHE_ROOT"] = "new-cache"
            self.assertEqual(environment_value("MORAP_CACHE_ROOT"), "new-cache")
            os.environ["MORAP_CACHE_ROOT"] = ""
            self.assertEqual(environment_value("MORAP_CACHE_ROOT"), "")

    def test_archived_helpers_receive_current_environment_settings(self):
        original = {"LIN_MNP_CACHE_ROOT": "old", "MORAP_CACHE_ROOT": "new"}
        result = compatible_environment(original)
        self.assertEqual(result["LIN_MNP_CACHE_ROOT"], "new")
        self.assertEqual(result["MORAP_CACHE_ROOT"], "new")
        self.assertEqual(original["LIN_MNP_CACHE_ROOT"], "old")
        self.assertEqual(
            compatible_environment({"LIN_MNP_CACHE_ROOT": "old"})["MORAP_CACHE_ROOT"],
            "old",
        )

    def test_archive_paths_prefer_current_files_and_fall_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "benchmark/lin_mnp/metrics.csv"
            current = root / "benchmark/morap/metrics.csv"
            self.assertEqual(artifact_path(current), current)
            legacy.parent.mkdir(parents=True)
            legacy.write_text("historical\n")
            self.assertEqual(artifact_path(current), legacy)
            current.parent.mkdir(parents=True)
            current.write_text("current\n")
            self.assertEqual(artifact_path(current), current)

    def test_prediction_fields_prefer_current_and_reject_missing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions.npz"
            np.savez(path, morap=np.ones((2, 1)), lin_mnp=np.zeros((2, 1)))
            with np.load(path, allow_pickle=False) as archive:
                np.testing.assert_array_equal(artifact_value(archive, "morap"), 1)
        with self.assertRaises(KeyError):
            artifact_value({"target": np.ones((2, 1))}, "morap")

    def test_inference_reads_both_checkpoint_names_and_writes_current_name(self):
        dataset = SimpleNamespace(
            patch_indices=[0, 1], sections=["S1", "S2"], barcodes=["a", "b"],
            context_array=lambda: np.ones((2, 3), dtype=np.float32),
        )
        prediction = np.asarray([[1], [2]], dtype=np.float32)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for identity in ("Lin-MNP", "MoRAP"):
                with self.subTest(identity=identity):
                    checkpoint = root / f"{identity}.pt"
                    torch.save({
                        "scientific_model_identity": identity,
                        "shared_artifact": {}, "genes": ["G1"],
                    }, checkpoint)
                    original_hash = model.sha256(checkpoint)
                    output = root / f"{identity}.npz"
                    with (
                        patch.object(model, "load_local_cache", return_value=np.ones((2, 3))),
                        patch.object(model, "InferenceSpotDataset", return_value=dataset),
                        patch.object(model, "forward", return_value=prediction),
                        contextlib.redirect_stdout(io.StringIO()),
                    ):
                        record = model.infer(checkpoint, ["S1", "S2"], output)
                    self.assertEqual(record["scientific_model_identity"], "MoRAP")
                    self.assertEqual(record["morap_array_sha256"], model.array_sha256(prediction))
                    self.assertEqual(model.sha256(checkpoint), original_hash)
                    with np.load(output, allow_pickle=False) as archive:
                        self.assertIn("morap", archive.files)
                        self.assertNotIn("lin_mnp", archive.files)
                        np.testing.assert_array_equal(archive["morap"], prediction)

            invalid = root / "invalid.pt"
            torch.save({"scientific_model_identity": "different-model"}, invalid)
            with self.assertRaisesRegex(ValueError, "checkpoint identity"):
                model.infer(invalid, ["S1", "S2"], root / "invalid.npz")

    def test_evaluation_accepts_mixed_artifacts_and_keeps_checksum_validation(self):
        prediction = np.asarray([[1], [2], [3]], dtype=np.float32)
        dataset = SimpleNamespace(
            sections=("S1",) * 3, barcodes=("a", "b", "c"), genes=("G1",),
            target_matrix=prediction,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folds = [
                {"fold_id": i, "test_patient_id": f"P{i}", "test_sample_ids": ["S1"]}
                for i in range(4)
            ]
            split = root / "folds.json"
            split.write_text(json.dumps({"folds": folds}))
            config = dict(model.CONFIG, folds=split)
            manifests = {"folds": model.sha256(split)}
            for config_key, manifest_key in (
                ("patch_cache", "raw_patches"), ("foundation_cache", "context"),
                ("local_core_manifest", "local"),
            ):
                manifest = root / manifest_key / "manifest.json"
                manifest.parent.mkdir()
                manifest.write_text("{}")
                config[config_key] = manifest if manifest_key == "local" else manifest.parent
                manifests[manifest_key] = model.sha256(manifest)

            for fold in folds:
                run = root / f"fold{fold['fold_id']}"
                run.mkdir()
                key = "lin_mnp" if fold["fold_id"] % 2 == 0 else "morap"
                archive = run / "outer_test_predictions.npz"
                np.savez(archive, **{
                    key: prediction, "pointwise": prediction,
                    "sections": dataset.sections, "barcodes": dataset.barcodes,
                    "genes": dataset.genes,
                })
                checkpoint = run / "checkpoint.pt"
                torch.save({}, checkpoint)
                metadata = {
                    "fold": fold["fold_id"], "patient": fold["test_patient_id"],
                    "outer_test_labels_accessed": False,
                    "input_manifest_sha256": manifests,
                    "checkpoint_sha256": model.sha256(checkpoint),
                    "pointwise_array_sha256": model.array_sha256(prediction),
                    f"{key}_array_sha256": model.array_sha256(prediction),
                }
                metadata_path = run / "run_metadata.json"
                metadata_path.write_text(json.dumps(metadata))
                (run / "complete.json").write_text(json.dumps({
                    "run_metadata_sha256": model.sha256(metadata_path),
                    "prediction_file_sha256": model.sha256(archive),
                }))

            with (
                patch.object(model, "LabeledSpotDataset", return_value=dataset),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = model.evaluate_folds(root, config)
            self.assertEqual(set(result["summary"]), {"morap", "linear_readout"})
            self.assertAlmostEqual(result["summary"]["morap"]["mean_pcc"], 1.0)

            (root / "evaluation.json").unlink()
            (root / "fold0/outer_test_predictions.npz").write_bytes(b"corrupted")
            with patch.object(model, "LabeledSpotDataset") as labels:
                with self.assertRaisesRegex(ValueError, "prediction checksum"):
                    model.evaluate_folds(root, config)
                labels.assert_not_called()


if __name__ == "__main__":
    unittest.main()
