"""
Download BIRD Databases for Evaluation

This script downloads the BIRD benchmark databases needed for execution verification.
Note: Some databases may require authentication or have usage restrictions.

Usage:
    python download_bird_databases.py --output-dir data/databases
"""

import os
import wget
import zipfile
import argparse
from pathlib import Path
from typing import List


class BIRDDatabaseDownloader:
    """Download BIRD benchmark databases"""
    
    def __init__(self, output_dir: str = "data/databases"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # BIRD database URLs (from official GitHub)
        self.train_databases_url = "https://bird-bench.github.io/data/train_databases.zip"
        self.dev_databases_url = "https://bird-bench.github.io/data/dev_databases.zip"
        
        # Alternative: Individual databases (if full download fails)
        self.individual_dbs = {
            "user_preferences": "https://bird-bench.github.io/data/train_databases/user_preferences.zip",
            "student_club": "https://bird-bench.github.io/data/train_databases/student_club.zip",
            # Add more as needed
        }
    
    def download_train_databases(self) -> bool:
        """Download all training databases"""
        print(f"\n{'='*60}")
        print("Downloading BIRD Training Databases")
        print('='*60)
        
        output_path = self.output_dir / "train_databases.zip"
        
        try:
            print(f"Downloading from {self.train_databases_url}")
            wget.download(self.train_databases_url, str(output_path))
            
            print(f"\nExtracting to {self.output_dir / 'train_databases'}")
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir / 'train_databases')
            
            # Clean up
            output_path.unlink()
            
            print(f"✓ Downloaded and extracted training databases")
            return True
            
        except Exception as e:
            print(f"✗ Failed to download training databases: {e}")
            return False
    
    def download_dev_databases(self) -> bool:
        """Download all development databases"""
        print(f"\n{'='*60}")
        print("Downloading BIRD Development Databases")
        print('='*60)
        
        output_path = self.output_dir / "dev_databases.zip"
        
        try:
            print(f"Downloading from {self.dev_databases_url}")
            wget.download(self.dev_databases_url, str(output_path))
            
            print(f"\nExtracting to {self.output_dir / 'dev_databases'}")
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir / 'dev_databases')
            
            # Clean up
            output_path.unlink()
            
            print(f"✓ Downloaded and extracted development databases")
            return True
            
        except Exception as e:
            print(f"✗ Failed to download development databases: {e}")
            return False
    
    def download_mini_dev_databases(self) -> bool:
        """Download Mini-Dev databases (3 dialects)"""
        print(f"\n{'='*60}")
        print("Downloading Mini-Dev Databases (3 dialects)")
        print('='*60)
        
        mini_dev_dir = self.output_dir / "mini_dev"
        mini_dev_dir.mkdir(parents=True, exist_ok=True)
        
        # Mini-Dev has 3 dialects: SQLite, MySQL, PostgreSQL
        dialects = ["sqlite", "mysql", "postgresql"]
        
        for dialect in dialects:
            print(f"\nDownloading {dialect} dialect...")
            url = f"https://bird-bench.github.io/data/mini_dev_{dialect}.zip"
            output_path = mini_dev_dir / f"{dialect}.zip"
            
            try:
                wget.download(url, str(output_path))
                
                print(f"\nExtracting {dialect}...")
                with zipfile.ZipFile(output_path, 'r') as zip_ref:
                    zip_ref.extractall(mini_dev_dir / dialect)
                
                output_path.unlink()
                print(f"✓ Downloaded {dialect} dialect")
                
            except Exception as e:
                print(f"✗ Failed to download {dialect}: {e}")
        
        return True
    
    def verify_databases(self) -> dict:
        """Verify downloaded databases"""
        print(f"\n{'='*60}")
        print("Verifying Downloaded Databases")
        print('='*60)
        
        verification = {
            'train_databases': False,
            'dev_databases': False,
            'mini_dev': False
        }
        
        # Check train databases
        train_dir = self.output_dir / "train_databases"
        if train_dir.exists():
            db_count = len(list(train_dir.glob("*.db")))
            print(f"Train databases: {db_count} databases found")
            verification['train_databases'] = db_count > 0
        
        # Check dev databases
        dev_dir = self.output_dir / "dev_databases"
        if dev_dir.exists():
            db_count = len(list(dev_dir.glob("*.db")))
            print(f"Dev databases: {db_count} databases found")
            verification['dev_databases'] = db_count > 0
        
        # Check mini_dev
        mini_dev_dir = self.output_dir / "mini_dev"
        if mini_dev_dir.exists():
            for dialect in ["sqlite", "mysql", "postgresql"]:
                dialect_dir = mini_dev_dir / dialect
                if dialect_dir.exists():
                    db_count = len(list(dialect_dir.glob("*.db")))
                    print(f"Mini-Dev ({dialect}): {db_count} databases found")
                    verification['mini_dev'] = verification['mini_dev'] or db_count > 0
        
        return verification
    
    def download_all(self):
        """Download all databases"""
        print("\n" + "="*80)
        print("BIRD Database Downloader")
        print("="*80)
        
        # Try to download all
        self.download_train_databases()
        self.download_dev_databases()
        self.download_mini_dev_databases()
        
        # Verify
        verification = self.verify_databases()
        
        print(f"\n{'='*60}")
        print("Download Summary")
        print('='*60)
        
        for dataset, success in verification.items():
            status = "✓" if success else "✗"
            print(f"{status} {dataset}: {'Success' if success else 'Failed'}")
        
        # If official download failed, try alternatives
        if not any(verification.values()):
            print(f"\n{'='*60}")
            print("Official BIRD databases unavailable.")
            print("Falling back to sample databases...")
            print('='*60)
            
            self.create_sample_databases()
    
    def create_sample_databases(self):
        """Create sample databases for testing (fallback)"""
        print("\nCreating sample databases for testing...")
        
        sample_dir = self.output_dir / "sample_databases"
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Run the sample database creation script
        import subprocess
        result = subprocess.run(
            ["python", "data/create_sample_databases.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Sample databases created successfully")
        else:
            print(f"✗ Failed to create sample databases: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description='Download BIRD databases')
    parser.add_argument('--output-dir', type=str, default='data/databases',
                       help='Output directory for databases')
    
    args = parser.parse_args()
    
    downloader = BIRDDatabaseDownloader(args.output_dir)
    downloader.download_all()


if __name__ == '__main__':
    main()
