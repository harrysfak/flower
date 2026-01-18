import os
import shutil
from typing import Iterable, Optional, Callable


class FileManager:
    """
    Manage files in a working directory (e.g., an unzipped image folder).

    Methods
    -------
    reset_memory(keep: Optional[Iterable[str]] = None,
                 predicate: Optional[Callable[[str], bool]] = None,
                 dry_run: bool = False) -> list[str]
        Deletes files and folders inside the working directory.
        - keep: collection of basenames to skip.
        - predicate: function(path) -> bool to decide whether to delete an entry.
        - dry_run: if True, returns what would be deleted without deleting.

    Notes
    -----
    - Only contents of the directory are removed; the directory itself is preserved.
    - Directories are removed recursively.
    """

    def __init__(self, unzip_dir: str):
        if not unzip_dir:
            raise ValueError("unzip_dir must be a non-empty path.")
        self.unzip_dir = os.path.abspath(unzip_dir)
        if not os.path.isdir(self.unzip_dir):
            raise NotADirectoryError(f"Path does not exist or is not a directory: {self.unzip_dir}")

    def reset_memory(
            self,
            keep: Optional[Iterable[str]] = None,
            predicate: Optional[Callable[[str], bool]] = None,
            dry_run: bool = False
    ) -> list[str]:
        """
        Delete the contents of `self.unzip_dir` with optional filters.

        Parameters
        ----------
        keep : Optional[Iterable[str]]
            Basenames to preserve (e.g., {'.gitkeep', 'README.md'}).
        predicate : Optional[Callable[[str], bool]]
            A function that receives an absolute path and returns True if it should be deleted.
            If None, all entries (except those in `keep`) are deleted.
        dry_run : bool
            If True, only returns the list of paths that would be deleted.

        Returns
        -------
        list[str]
            The list of absolute paths deleted (or that would be deleted in dry_run).
        """
        keep_set = set(keep or [])
        to_delete: list[str] = []

        # Build list of absolute paths to delete
        for name in os.listdir(self.unzip_dir):
            if name in keep_set:
                continue
            path = os.path.join(self.unzip_dir, name)
            if predicate is not None and not predicate(path):
                continue
            to_delete.append(path)

        if dry_run:
            return to_delete

        deleted: list[str] = []
        for path in to_delete:
            try:
                if os.path.isdir(path) and not os.path.islink(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted.append(path)
            except FileNotFoundError:
                # Skip if already gone (race conditions, etc.)
                continue
            except PermissionError as e:
                # Surface helpful error with context
                raise PermissionError(f"Permission denied while deleting: {path}") from e
            except OSError as e:
                # Catch other OS-level errors
                raise OSError(f"Failed to delete: {path} ({e})") from e

        return deleted
