import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services import nvidia


class NvidiaServiceTests(unittest.TestCase):
    def setUp(self):
        self.previous_key = os.environ.get("NVIDIA_API_KEY")
        os.environ["NVIDIA_API_KEY"] = "test-key"
        nvidia.reset_client_cache()

    def tearDown(self):
        if self.previous_key is None:
            os.environ.pop("NVIDIA_API_KEY", None)
        else:
            os.environ["NVIDIA_API_KEY"] = self.previous_key
        nvidia.reset_client_cache()

    @patch("app.services.nvidia.OpenAI")
    def test_complete_uses_nvidia_model_and_parameters(self, openai_cls):
        fake_client = openai_cls.return_value
        fake_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
        )

        result = nvidia.complete([{"role": "user", "content": "hola"}], max_tokens=123)

        self.assertEqual(result, '{"ok": true}')
        openai_cls.assert_called_once()
        kwargs = fake_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "qwen/qwen3.5-397b-a17b")
        self.assertEqual(kwargs["max_tokens"], 123)
        self.assertFalse("test-key" in str(kwargs))

    @patch("app.services.nvidia.complete", return_value="```json\n{\"value\": 1}\n```")
    def test_json_completion_accepts_fenced_json(self, _complete):
        self.assertEqual(nvidia.json_completion([]), {"value": 1})

    def test_missing_key_is_a_safe_error(self):
        os.environ.pop("NVIDIA_API_KEY")
        nvidia.reset_client_cache()
        with self.assertRaises(nvidia.NvidiaServiceError):
            nvidia.complete([])
