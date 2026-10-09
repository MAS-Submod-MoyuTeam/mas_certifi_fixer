init -990 python:
    certifi_fixer_submod = store.mas_submod_utils.Submod(
        author="P",
        name="CertifiFixer",
        version="1.0.1",
        description="Restores the bundled certifi package when MAS cannot import it."
    )

init -100 python:
    """
    CertifiFixer

    Keep MAS's normal certifi import path untouched when it works. If the
    startup probe reports that certifi is unavailable, replace the files in
    game/python-packages/certifi with the copy shipped by this submod.
    """
    import os
    import shutil
    import store



    def _certifi_fixer_replace_certifi():
        if store.mas_can_import.certifi():
            return False

        game_dir = renpy.config.gamedir
        source_dir = os.path.join(
            game_dir, "Submods", "CertifiFixer", "certifi"
        )
        target_dir = os.path.join(game_dir, "python-packages", "certifi")

        if not os.path.isdir(source_dir):
            store.mas_logging.init_log("submod_log").error(
                "CertifiFixer source directory missing: {0}".format(source_dir)
            )
            return False

        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

        for root, dirs, files in os.walk(source_dir):
            relative_root = os.path.relpath(root, source_dir)
            destination_root = target_dir
            if relative_root != ".":
                destination_root = os.path.join(target_dir, relative_root)
            if not os.path.isdir(destination_root):
                os.makedirs(destination_root)
            for filename in files:
                shutil.copy2(
                    os.path.join(root, filename),
                    os.path.join(destination_root, filename)
                )

        store.mas_logging.init_log("submod_log").warning(
            "CertifiFixer replaced python-packages/certifi from {0}".format(
                source_dir
            )
        )
        return True

    _certifi_fixer_replace_certifi()
