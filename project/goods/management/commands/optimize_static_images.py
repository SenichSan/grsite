import os
import glob
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image
from common.image_utils import save_avif_optimized, save_webp, ensure_dir


class Command(BaseCommand):
    help = "Optimize static images (backgrounds, hero images) with aggressive AVIF compression"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be optimized without actually doing it',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=12,
            help='AVIF quality for background images (default: 12)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if AVIF files already exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quality = options['quality']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No files will be modified"))
        
        # Define static image directories to scan
        static_dirs = [
            os.path.join(settings.BASE_DIR, 'static'),
            os.path.join(settings.MEDIA_ROOT),
        ]
        
        # Image patterns to look for
        patterns = ['*.png', '*.jpg', '*.jpeg']
        
        # Files that should be treated as backgrounds (aggressive compression)
        background_patterns = [
            '*bg*', '*background*', '*hero*', '*banner*', 
            'seo-text-bg*', '*texture*', '*pattern*'
        ]
        
        total_processed = 0
        total_size_before = 0
        total_size_after = 0
        
        self.stdout.write(f"\n🔍 Scanning for static images to optimize...")
        
        for static_dir in static_dirs:
            if not os.path.exists(static_dir):
                continue
                
            self.stdout.write(f"\n📁 Scanning: {static_dir}")
            
            for pattern in patterns:
                search_pattern = os.path.join(static_dir, '**', pattern)
                files = glob.glob(search_pattern, recursive=True)
                
                for file_path in files:
                    try:
                        # Skip if already processed or is a variant
                        if any(suffix in file_path for suffix in ['_128.', '_400x300.', '_800x600.']):
                            continue
                        
                        # Skip problematic files
                        filename_lower = os.path.basename(file_path).lower()
                        if any(skip in filename_lower for skip in ['not found', 'baseavatar', 'temp', 'cache']):
                            continue
                            
                        # Get original file size
                        original_size = os.path.getsize(file_path)
                        total_size_before += original_size
                        
                        # Determine image type based on filename
                        filename = os.path.basename(file_path).lower()
                        is_background = any(pattern.replace('*', '') in filename 
                                          for pattern in background_patterns)
                        
                        image_type = "background" if is_background else "product"
                        
                        # Generate optimized paths
                        root, ext = os.path.splitext(file_path)
                        avif_path = f"{root}.avif"
                        webp_path = f"{root}.webp"
                        
                        # Check if we need to process
                        needs_processing = not os.path.exists(avif_path) or force
                        
                        if not needs_processing:
                            existing_size = os.path.getsize(avif_path)
                            # If existing AVIF is large, regenerate it
                            if existing_size > 200000:  # 200KB threshold
                                needs_processing = True
                                self.stdout.write(f"🔄 Large AVIF detected ({existing_size//1024}KB), will regenerate")
                        
                        if not needs_processing:
                            continue
                        
                        if dry_run:
                            self.stdout.write(
                                f"🔍 Would optimize: {filename} "
                                f"({original_size//1024}KB, type: {image_type})"
                            )
                            total_processed += 1
                            continue
                        
                        # Open and process image
                        with Image.open(file_path) as img:
                            # Convert to RGB if necessary
                            if img.mode in ('RGBA', 'LA', 'P'):
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = rgb_img
                            
                            # For very large images, resize first
                            max_size = 1920 if is_background else 1200
                            if max(img.size) > max_size:
                                ratio = max_size / max(img.size)
                                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                                img = img.resize(new_size, Image.Resampling.LANCZOS)
                                self.stdout.write(f"📏 Resized to {new_size}")
                            
                            # Save optimized AVIF
                            save_avif_optimized(img, avif_path, image_type=image_type)
                            
                            # Save WebP as fallback
                            webp_quality = 70 if is_background else 80
                            save_webp(img, webp_path, quality=webp_quality)
                        
                        # Calculate size after
                        if os.path.exists(avif_path):
                            new_size = os.path.getsize(avif_path)
                            total_size_after += new_size
                            reduction = ((original_size - new_size) / original_size) * 100
                            
                            self.stdout.write(
                                f"✅ {filename}: {original_size//1024}KB → {new_size//1024}KB "
                                f"(-{reduction:.1f}%, type: {image_type})"
                            )
                        else:
                            total_size_after += original_size
                            self.stdout.write(f"⚠️  Failed to create AVIF for {filename}")
                        
                        total_processed += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error processing {file_path}: {e}")
                        )
        
        # Summary
        self.stdout.write(f"\n📊 Summary:")
        if dry_run:
            self.stdout.write(f"   Would process: {total_processed} images")
            self.stdout.write(f"   Total size: {total_size_before//1024//1024}MB")
            self.stdout.write(f"   Run without --dry-run to actually optimize")
        else:
            if total_size_before > 0:
                total_reduction = ((total_size_before - total_size_after) / total_size_before) * 100
                self.stdout.write(f"   Processed: {total_processed} images")
                self.stdout.write(f"   Size before: {total_size_before//1024//1024}MB")
                self.stdout.write(f"   Size after: {total_size_after//1024//1024}MB")
                self.stdout.write(f"   Total reduction: {total_reduction:.1f}%")
                self.stdout.write(f"   Saved: {(total_size_before-total_size_after)//1024//1024}MB")
            else:
                self.stdout.write(f"   No images processed")
        
        self.stdout.write(f"\n💡 Tips:")
        self.stdout.write(f"   • Use --quality 8 for even more aggressive compression")
        self.stdout.write(f"   • Background images use quality={quality} by default")
        self.stdout.write(f"   • Check visual quality after optimization")
