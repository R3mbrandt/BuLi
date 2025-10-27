"""
Simple file-based cache for Transfermarkt data
Reduces scraping frequency and speeds up predictions
"""

import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import os


class DataCache:
    """
    File-based cache with expiry support
    Stores data in pickle format for speed
    """

    def __init__(self, cache_dir: str = ".cache", default_expiry_hours: int = 24):
        """
        Initialize cache

        Args:
            cache_dir: Directory to store cache files
            default_expiry_hours: Default expiry time in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_expiry_hours = default_expiry_hours

    def _get_cache_path(self, key: str) -> Path:
        """
        Get cache file path for a key

        Args:
            key: Cache key (e.g., "squad_value_bayern")

        Returns:
            Path to cache file
        """
        # Sanitize key for filename
        safe_key = key.replace('/', '_').replace(' ', '_').lower()
        return self.cache_dir / f"{safe_key}.pkl"

    def get(self, key: str, expiry_hours: Optional[int] = None) -> Optional[Any]:
        """
        Get cached data if not expired

        Args:
            key: Cache key
            expiry_hours: Custom expiry time (uses default if None)

        Returns:
            Cached data or None if expired/not found
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cached = pickle.load(f)

            # Check expiry
            cached_time = cached.get('timestamp')
            if not cached_time:
                return None

            expiry = expiry_hours if expiry_hours is not None else self.default_expiry_hours
            expiry_time = cached_time + timedelta(hours=expiry)

            if datetime.now() > expiry_time:
                # Expired - remove cache file
                cache_path.unlink()
                return None

            return cached.get('data')

        except Exception as e:
            # If cache is corrupted, remove it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, key: str, data: Any) -> bool:
        """
        Save data to cache

        Args:
            key: Cache key
            data: Data to cache (must be picklable)

        Returns:
            True if successful
        """
        cache_path = self._get_cache_path(key)

        try:
            cached = {
                'timestamp': datetime.now(),
                'data': data
            }

            with open(cache_path, 'wb') as f:
                pickle.dump(cached, f)

            return True

        except Exception as e:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete cached data

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            cache_path.unlink()
            return True

        return False

    def clear_all(self) -> int:
        """
        Clear all cached data

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            count += 1
        return count

    def get_cache_info(self) -> dict:
        """
        Get information about cached files

        Returns:
            Dictionary with cache statistics
        """
        info = {
            'cache_dir': str(self.cache_dir),
            'total_files': 0,
            'total_size_bytes': 0,
            'files': []
        }

        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                size = cache_file.stat().st_size
                modified = datetime.fromtimestamp(cache_file.stat().st_mtime)

                # Try to load to get expiry info
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                    timestamp = cached.get('timestamp', modified)
                    expiry = timestamp + timedelta(hours=self.default_expiry_hours)
                    is_expired = datetime.now() > expiry

                info['files'].append({
                    'name': cache_file.name,
                    'size_bytes': size,
                    'cached_at': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'expires_at': expiry.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_expired': is_expired
                })

                info['total_files'] += 1
                info['total_size_bytes'] += size

            except Exception:
                continue

        return info


# Global cache instance
_cache = None


def get_cache(cache_dir: str = ".cache", expiry_hours: int = 24) -> DataCache:
    """
    Get global cache instance

    Args:
        cache_dir: Directory for cache files
        expiry_hours: Default expiry time

    Returns:
        DataCache instance
    """
    global _cache
    if _cache is None:
        _cache = DataCache(cache_dir, expiry_hours)
    return _cache
