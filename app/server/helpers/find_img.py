from pathlib import Path


def find_image_dir(dataset_root: Path) -> Path:
    # 1) αν έχει εικόνες απευθείας στο root
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
    if any(p.suffix.lower() in exts for p in dataset_root.iterdir() if p.is_file()):
        return dataset_root

    # 2) αν έχει 1 φάκελο μέσα (τύπου TOpLOAD) με εικόνες
    subdirs = [p for p in dataset_root.iterdir() if p.is_dir()]
    for d in subdirs:
        if any(p.suffix.lower() in exts for p in d.rglob("*") if p.is_file()):
            return d

    # 3) fallback: ψάξε οπουδήποτε μέσα
    for p in dataset_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            return p.parent

    raise FileNotFoundError("No images found in dataset directory.")
