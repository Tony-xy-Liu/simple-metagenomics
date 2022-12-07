import sys
import numpy as np

_, fpath, amnt, out_path = sys.argv
amnt = float(amnt)
fname = fpath.split('/')[-1]
fdir = "/".join(fpath.split('/')[:-1])

ENTRY_HEAD = '@' if fname.split('.')[-1] in ["fastq", "fq"] else '>' # fa

print(fpath)
print('ss to', amnt*100, 'pct')


np.random.seed(12345)
def should_keep():
    return np.random.random() <= amnt

with open(fpath) as f:
    with open(out_path, 'w') as out:
        keep = should_keep()
        for i, line in enumerate(f):
            if line[0] == ENTRY_HEAD: keep = should_keep()
            if not keep: continue

            out.write(line)
