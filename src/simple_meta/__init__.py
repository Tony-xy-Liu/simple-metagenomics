import os, sys
import argparse
import subprocess
import signal
import time

IMAGE = 'simple-metagenomics'
URL = f"quay.io/txyliu/{IMAGE}:latest"
LINE = "################################################################"
class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))

def print_header():
    print(f"""\
{LINE}
simple metagnomics
v1.0

This shell is not live
Please be patient!
{LINE}
    """)

def shell_docker(ref_dir, out_dir, cmd):
            # --mount type=bind,source="/home/tony/workspace/python/grad/simple-metagenomics/docker/load",target="/app" \
    proc = subprocess.Popen([f"""\
        docker run --rm \
            -e XDG_CACHE_HOME="/ws/" \
            --mount type=bind,source="{out_dir}",target="/ws"\
            --mount type=bind,source="{ref_dir}",target="/ref"\
            --mount type=bind,source="{ref_dir}/.ncbi",target="/.ncbi"\
            --workdir="/ws" \
            -u $(id -u):$(id -g) \
            {URL} \
            /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && conda run -n main {cmd}"
    """], shell=True)
    def handler(signum, frame):
        proc.terminate()
        os.system(f"""\
            CID=$(docker ps | grep quay.io/txyliu/simple-metagenomics:latest | cut -c1-12 -)
            docker stop $CID
            rm {out_dir}/.snakemake/locks/*
        """)
    signal.signal(signal.SIGINT, handler)
    while proc.poll() is None:
        time.sleep(1)

def shell_singularity(ref_dir, out_dir, cmd):
    return os.system(f"""\
        export XDG_CACHE_HOME="/ws"
        singularity exec \
            --bind {out_dir}:/ws,{ref_dir}:/ref,{ref_dir}/.ncbi:/.ncbi \
            --workdir "/ws" \
            {ref_dir}/{IMAGE}.sif \
            /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && conda run -n main {cmd}"
    """)

def setup():
    parser = ArgumentParser(prog='smg setup')

    parser.add_argument('-r', metavar='PATH', help="where to save required resources", required=True)
    parser.add_argument('-c', metavar='TYPE',
        choices=["singularity", "docker"],
        help='the resource container type, choose from: "singularity" (default) or "docker"',
        default="singularity")

    args = parser.parse_args(sys.argv[2:])
    ref_path = os.path.abspath(args.r)
    ncbi_ref = f'{ref_path}/.ncbi'
    if not os.path.exists(ncbi_ref):
        os.makedirs(ncbi_ref, exist_ok=True)

    if args.c == 'singularity':
        image_path = f'{ref_path}/{IMAGE}.sif'
        if os.path.exists(image_path):
            os.remove(image_path)
        success = 0==os.system(f"""\
            singularity pull {ref_path}/{IMAGE}.sif docker://{URL}
        """)
        if success:
            shell_singularity(ref_path, ref_path, "/app/setup.sh")
        else:
            print('singularity pull failed')
    else: # docker
        success = 0==os.system(f"""\
            docker pull {URL} \
        """)
        if success:
            shell_docker(ref_path, ref_path, "/app/setup.sh")
        else:
            print('docker pull failed')


def run():
    parser = ArgumentParser(
        prog = 'smg run',
        # description = "v1.0",
        # epilog = 'Text at the bottom of help',
    )

    # parser.add_argument('-1', metavar='FASTQ', help="paried-end fastq reads 1", required=True)
    # parser.add_argument('-2', metavar='FASTQ', help="paried-end fastq reads 2", required=True)
    parser.add_argument('-r', metavar='PATH', help="path to saved required resources from running: smg setup", required=True)
    parser.add_argument('-i', metavar='SRA_ID', help="example: SRR19573024", required=True)
    parser.add_argument('-o', metavar='PATH', help="output folder", required=True)
    parser.add_argument('-s', metavar='DECIMAL', type=float, help="subsample fraction for raw reads, set to 1 for no subsampling, default:0.01", default=0.01 )
    parser.add_argument('-t', metavar='INT', type=int, help="threads, default:16", default=16)
    parser.add_argument('--mock', help="dry run snakemake", 
        action='store_true', default=False, required=False)

    args = parser.parse_args(sys.argv[2:])
    if not os.path.exists(args.r):
        print(f"reference folder doesn't exist: {args.r}\ntry: smg setup")
        return
    os.makedirs(args.o, exist_ok=True)
    ref_path = os.path.abspath(args.r)
    out_path = os.path.abspath(args.o)

    subsample = min(1, args.s)

    cmd = f"""\
        snakemake -s /app/main.smk --configfile /app/config.yaml -d /ws\
            {"-n" if args.mock else ""} \
            --config sample={args.i} ss={subsample} \
            --keep-going --keep-incomplete --cores {args.t}"""

    print_header()
    if os.path.exists(f'{ref_path}/{IMAGE}.sif'):
        success = 0==shell_singularity(ref_path, out_path, cmd)
    else:
        success = 0==shell_docker(ref_path, out_path, cmd)
    if success and not args.mock:
        print(f"{LINE}\nsubsample rate: {args.s}\nfinal output at\n{out_path}/{args.i}/diamond/")

def help():
    print("""\
simple-metagenomics v1.0
https://github.com/Tony-xy-Liu/simple-metagenomics

Syntax: smg COMMAND [OPTIONS]

Where COMMAND is one of:
setup
run

for additional help, use:
smg COMMAND -h
""")

def main():
    if len(sys.argv) <= 1:
        help()
        return

    { # switch
        "setup": setup,
        "run": run,
    }.get(
        sys.argv[1], 
        help # default
    )()
