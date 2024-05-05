import sys
import os
from .core import UIComponent
from .transformers.jinja import JinjaTransfomer


indir = sys.argv[1]
outdir = sys.argv[2]
transfomer = JinjaTransfomer()
for filename in os.listdir(indir):
    if not os.path.isfile(os.path.join(indir, filename)):
        continue
    component = UIComponent.from_file(os.path.join(indir, filename))
    with open(os.path.join(outdir, filename), "w") as f:
        f.write(transfomer.transform(component))