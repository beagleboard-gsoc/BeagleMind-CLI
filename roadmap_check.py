import os
import glob

print("🔍 BEAGLEMIN D ROADMAP CHECK")
print("="*50)

# Check dataset
dataset_files = glob.glob("data/*.jsonl")
print(f"📊 Datasets: {len(dataset_files)} files")
for f in dataset_files:
    size = os.path.getsize(f)
    print(f"  - {f}: {size/1e6:.1f}MB")

# Check CLI commands
os.system("beaglemind --help")

# Check for forum/discord scrapers
scrapers = glob.glob("*scrape*.py") + glob.glob("*forum*.py")
print(f"\n🕷️  Scrapers found: {len(scrapers)}")
print(scrapers)

# Check fine-tuning
ft_files = glob.glob("*fine*.py") + glob.glob("*train*.py")
print(f"\n🤖 Fine-tuning: {len(ft_files)} files")
print(ft_files)

# Check RAG config
print("\n🎛️  RAG Config check:")
if os.path.exists("config.py") or "config" in open("app.py").read():
    print("✅ Config found")
else:
    print("❌ Config missing")
