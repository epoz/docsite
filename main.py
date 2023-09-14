import os, zipfile, logging, tempfile, hashlib, sys
import panflute, pypandoc, io
from markupsafe import Markup
import jinja2

if os.environ.get("DEBUG") is not None:
    logging.basicConfig(level=logging.DEBUG)


TEMPLATE_PATH = "templates"
OUT_PATH = os.environ.get("OUT_PATH", "_")
if OUT_PATH.endswith("/"):
    OUT_PATH = OUT_PATH[:-1]
if not os.path.exists(OUT_PATH):
    os.mkdir(OUT_PATH)
    os.mkdir(os.path.join(OUT_PATH, "media"))


logging.debug("Getting zipfile")
ZIP_LOCATION = os.environ.get("ZIP_LOCATION")
if not ZIP_LOCATION:
    print("You need to specify env variable ZIP_LOCATION")
    sys.exit(1)

ROOT_PATH = os.environ.get("ROOT_PATH")
if not ROOT_PATH:
    print("You need to specify env variable ROOT_PATH")
    sys.exit(2)

logging.debug("Extracting zipfile")

found_root = 0
with zipfile.ZipFile(ZIP_LOCATION, "r") as zf:
    root_folder = zf.namelist()[0].split("/")[0]
    if root_folder == ROOT_PATH:
        for file in zf.namelist():
            if file.startswith(root_folder):
                found_root += 1
                zf.extract(file)
if found_root > 0:
    print(f"Extracted {found_root} files")
else:
    print(f"Nothing found in zip file for {ROOT_PATH}")
    sys.exit(3)

# os.unlink("x.zip")


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_PATH),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)
template = env.get_template(f"page.html")


def fixes(elem, doc, file_hashes):
    if isinstance(elem, panflute.Image):
        for afile, hfile in file_hashes.items():
            if elem.url.endswith(afile):
                elem.url = f"/media/{hfile}"
        elem.attributes = {}


logging.debug("Generating site")
for dirpath, dirnames, filenames in os.walk(ROOT_PATH):
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        if filename.endswith(".docx"):
            print(filepath)
            with tempfile.TemporaryDirectory() as tmpdir:
                data = pypandoc.convert_file(
                    filepath, "json", extra_args=[f"--extract-media={tmpdir}"]
                )
                tmpdir = os.path.join(tmpdir, "media")
                if os.path.exists(tmpdir):
                    media_files = [file for file in os.listdir(tmpdir)]
                    file_hashes = {}
                    for file in media_files:
                        mediafilepath = os.path.join(tmpdir, file)
                        with open(mediafilepath, mode="rb") as f:
                            file_contents = f.read()
                            file_hash = hashlib.md5(file_contents).hexdigest()
                            new_filename = f"{file_hash}.jpg"
                            new_filepath = os.path.join(tmpdir, new_filename)
                            os.rename(mediafilepath, new_filepath)
                            file_hashes[file] = new_filename
                        moved_filepath = os.path.join(OUT_PATH, "media", new_filename)
                        os.rename(new_filepath, moved_filepath)

            doc = panflute.load(io.StringIO(data))
            newdoc = panflute.run_filter(fixes, doc=doc, file_hashes=file_hashes)
            html = Markup(
                panflute.convert_text(
                    doc, input_format="panflute", output_format="html"
                )
            )
            outpath = filepath.replace(ROOT_PATH, OUT_PATH)
            if not os.path.exists(dirpath.replace(ROOT_PATH, OUT_PATH)):
                os.mkdir(dirpath.replace(ROOT_PATH, OUT_PATH))
            out = template.render({"content": Markup(html)})

            open(outpath.replace(".docx", ".html"), "w").write(out)
