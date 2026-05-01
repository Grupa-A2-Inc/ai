import builtins
import importlib.util
import os
import runpy
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch


def get_manage_path():
    return Path(__file__).resolve().parents[2] / "manage.py"


def load_manage_module():
    module_path = get_manage_path()
    spec = importlib.util.spec_from_file_location("manage", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ManageTests(TestCase):
    def test_main_sets_default_settings_and_delegates_to_django(self):
        manage = load_manage_module()
        execute_from_command_line = Mock()
        fake_management = type(sys)("django.core.management")
        fake_management.execute_from_command_line = execute_from_command_line

        with patch.dict(
            sys.modules,
            {"django.core.management": fake_management},
        ), patch.dict(
            os.environ,
            {},
            clear=True,
        ), patch.object(
            sys,
            "argv",
            ["manage.py", "check"],
        ):
            manage.main()

        self.assertEqual(
            execute_from_command_line.call_args.args,
            (["manage.py", "check"],),
        )

    def test_main_raises_helpful_error_when_django_cannot_be_imported(self):
        manage = load_manage_module()
        original_import = builtins.__import__

        def import_without_django(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "django.core.management":
                raise ImportError("No module named django")
            return original_import(name, globals, locals, fromlist, level)

        with patch.object(builtins, "__import__", import_without_django):
            with self.assertRaises(ImportError) as exc_info:
                manage.main()

        self.assertIn("Couldn't import Django", str(exc_info.exception))

    def test_script_entrypoint_calls_main(self):
        execute_from_command_line = Mock()
        fake_management = type(sys)("django.core.management")
        fake_management.execute_from_command_line = execute_from_command_line

        with patch.dict(
            sys.modules,
            {"django.core.management": fake_management},
        ), patch.object(
            sys,
            "argv",
            ["manage.py", "check"],
        ):
            runpy.run_path(str(get_manage_path()), run_name="__main__")

        self.assertEqual(
            execute_from_command_line.call_args.args,
            (["manage.py", "check"],),
        )
