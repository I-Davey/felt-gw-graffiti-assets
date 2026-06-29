import argparse
import csv
import os
from collections import defaultdict

from PIL import Image
from pypdf import PdfReader


DEFAULT_PDF = "Graffiti Removal - Fwys.pdf"
DEFAULT_CSV = "graffiti_jobs.csv"
DEFAULT_OUTPUT_DIR = "felt-gw-graffiti-assets"
PHOTO_SIZE = (640, 492)
MAX_IMAGE_COLUMNS = 12


def parse_pages(value):
    pages = []
    for part in (value or "").split(";"):
        part = part.strip()
        if part:
            pages.append(int(part))
    return pages


def read_jobs(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def ensure_site(output_dir):
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    with open(os.path.join(output_dir, ".nojekyll"), "w", encoding="utf-8") as marker:
        marker.write("")
    return image_dir


def save_photo(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rgb = image.convert("RGB")
    rgb.save(path, "JPEG", quality=78, optimize=True, progressive=True)


def extract_images(pdf_path, jobs, output_dir):
    image_dir = ensure_site(output_dir)
    reader = PdfReader(pdf_path)
    page_to_jobs = defaultdict(list)
    for row in jobs:
        for page in parse_pages(row.get("pdf_pages")):
            page_to_jobs[page].append(row["job_id"])

    job_counts = defaultdict(int)
    job_files = defaultdict(list)

    for page_number in sorted(page_to_jobs):
        if page_number < 1 or page_number > len(reader.pages):
            continue
        page = reader.pages[page_number - 1]
        job_id = page_to_jobs[page_number][0]
        photos = []
        for embedded in page.images:
            image = embedded.image
            if image.size == PHOTO_SIZE:
                photos.append(image)
        for photo in photos:
            job_counts[job_id] += 1
            filename = f"{job_id}_{job_counts[job_id]:02d}.jpg"
            relative = f"images/{job_id}/{filename}"
            save_photo(photo, os.path.join(output_dir, relative))
            job_files[job_id].append(relative.replace("\\", "/"))

    return job_files


def write_index(output_dir, jobs, job_files):
    total_images = sum(len(paths) for paths in job_files.values())
    total_jobs = sum(1 for row in jobs if job_files.get(row["job_id"]))
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        "  <title>GW Graffiti Felt Assets</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1f2933; }",
        "    a { color: #0b63ce; }",
        "    code { background: #f1f5f9; padding: 2px 5px; border-radius: 4px; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>GW Graffiti Felt Assets</h1>",
        f"  <p>Static image host for Felt popups. Contains {total_images} job photos across {total_jobs} jobs.</p>",
        "  <p>Use the generated CSV image URL columns when importing into Felt.</p>",
        "</body>",
        "</html>",
        "",
    ]
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as output:
        output.write("\n".join(lines))


def write_job_galleries(output_dir, jobs, job_files):
    jobs_dir = os.path.join(output_dir, "jobs")
    os.makedirs(jobs_dir, exist_ok=True)
    job_lookup = {row["job_id"]: row for row in jobs}
    for job_id, paths in job_files.items():
        row = job_lookup.get(job_id, {})
        title = f"Job {job_id}"
        subtitle = " - ".join(part for part in [row.get("asset_name", ""), row.get("located_on", "")] if part)
        lines = [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{title}</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 24px; color: #1f2933; background: #f8fafc; }",
            "    h1 { margin-bottom: 4px; }",
            "    .meta { color: #52606d; margin-bottom: 20px; }",
            "    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }",
            "    img { width: 100%; height: auto; display: block; background: white; border: 1px solid #d9e2ec; }",
            "    a { color: #0b63ce; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{title}</h1>",
            f"  <div class=\"meta\">{subtitle}</div>",
            "  <div class=\"grid\">",
        ]
        for path in paths:
            rel = "../" + path
            lines.append(f'    <a href="{rel}"><img src="{rel}" alt="{title} photo"></a>')
        lines.extend(["  </div>", "</body>", "</html>", ""])
        with open(os.path.join(jobs_dir, f"{job_id}.html"), "w", encoding="utf-8") as output:
            output.write("\n".join(lines))


def write_manifest(output_dir, job_files):
    path = os.path.join(output_dir, "image_manifest.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as output:
        writer = csv.writer(output)
        writer.writerow(["job_id", "image_count", "image_paths"])
        for job_id in sorted(job_files):
            writer.writerow([job_id, len(job_files[job_id]), ";".join(job_files[job_id])])


def main():
    parser = argparse.ArgumentParser(description="Extract embedded job photos for GitHub Pages/Felt.")
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = args.pdf if os.path.isabs(args.pdf) else os.path.join(script_dir, args.pdf)
    csv_path = args.csv if os.path.isabs(args.csv) else os.path.join(script_dir, args.csv)
    output_dir = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(script_dir, args.output_dir)

    jobs = read_jobs(csv_path)
    job_files = extract_images(pdf_path, jobs, output_dir)
    write_index(output_dir, jobs, job_files)
    write_job_galleries(output_dir, jobs, job_files)
    write_manifest(output_dir, job_files)
    print(f"Extracted {sum(len(paths) for paths in job_files.values())} images for {len(job_files)} jobs into {output_dir}")


if __name__ == "__main__":
    main()
