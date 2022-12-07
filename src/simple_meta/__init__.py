import os, sys
import argparse

URL = "quay.io/txyliu/simple-metagenomics:latest"
IMAGE = 'image'

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))

def shell_docker(ref_dir, out_dir, cmd):
    os.system(f"""\
        docker run -it --rm \
            -e XDG_CACHE_HOME="/ws/" \
            --mount type=bind,source="{out_dir}",target="/ws"\
            --mount type=bind,source="{ref_dir}",target="/ref"\
            --mount type=bind,source="{ref_dir}/.ncbi",target="/.ncbi"\
            --workdir="/ws" \
            -u $(id -u):$(id -g) \
            {URL} \
            mamba run -n main {cmd}
    """)

def setup():
    parser = ArgumentParser(prog='smg setup')

    parser.add_argument('-c', metavar='TYPE',
        choices=["singularity", "docker"],
        help="singularity or docker", required=True)
    parser.add_argument('-ref', metavar='PATH', help="where to save required resources", required=True)

    args = parser.parse_args(sys.argv[2:])
    # if os.path.exists(args.ref) and len(os.listdir())>0:
    #     print(f'{args.ref} is not empty, please use an empty folder' )

    def docker(ref_dir):
        os.system(f"""\
            docker pull {URL} \
        """)
        shell_docker(ref_dir, ref_dir, "cp -r /app/ncbi /ref/ && tar -xf /app/cog-20.fa.tar.gz -C /ref/")

    def singularity(ref_dir):
        # todo !!!!!!!!!!!
        os.system(f"""\
            singularity pull {ref_dir}/{IMAGE}.sif docker://{URL} \
            && singularity run {ref_dir}/{IMAGE}.sif
        """)

    ref_path = os.path.abspath(args.ref)
    if not os.path.exists(ref_path):
        os.makedirs(ref_path, exist_ok=True)
    if args.c == 'singularity':
        singularity(ref_path)
    else: # docker
        docker(ref_path)

def run():
    parser = ArgumentParser(
        prog = 'smg run',
        # description = "v1.0",
        # epilog = 'Text at the bottom of help',
    )

    # parser.add_argument('-1', metavar='FASTQ', help="paried-end fastq reads 1", required=True)
    # parser.add_argument('-2', metavar='FASTQ', help="paried-end fastq reads 2", required=True)
    parser.add_argument('-ref', metavar='PATH', help="where to save required resources", required=True)
    parser.add_argument('-i', metavar='SRA_ID', help="example: SRR22508334", required=True)
    parser.add_argument('-o', metavar='PATH', help="output folder", required=True)
    parser.add_argument('-s', metavar='DECIMAL', help="subsample fraction for raw reads, set to 1 for no subsampling, default:0.001", default=0.001 )
    parser.add_argument('-t', metavar='INT', help="default:16", default=16)

    args = parser.parse_args(sys.argv[2:])
    if not os.path.exists(args.ref):
        print(f"reference folder doesn't exist: {args.ref}\ntry: smg setup")
        return
    os.makedirs(args.o, exist_ok=True)

    # check for singularity image
    shell_docker(args.ref, args.o, )


def help():
    print("""\
simple-metagenomics v1.0
https://github.com/Tony-xy-Liu/simple-metagenomics

Syntax: smg COMMAND [OPTIONS]
options vary depending on command

Commands:
setup
run

Setup options:


Run options:


""")

def main():
    def entry_help():
        print("Error: Syntax: smg COMMAND [OPTIONS]. To print help message: smg -h")

    if len(sys.argv) == 1:
        entry_help()
        return

    { # switch
        "-h": help,
        "--help": help,
        "help": help,
        "setup": setup,
        "run": run,
    }.get(sys.argv[1], entry_help)()

    # parser = argparse.ArgumentParser(
    #     prog = 'smg setup',
    #     # description = "v1.0",
    #     # epilog = 'Text at the bottom of help',
    # )

    # parser.add_argument('-1', metavar='PATH', help="paried-end fastq reads 1", required=True)
    # parser.add_argument('-2', metavar='PATH', help="paried-end fastq reads 2", required=True)
    # parser.add_argument('-o', metavar='PATH', help="output folder", required=True)
    # parser.add_argument('-t', metavar='INT', help="threads to use, default:16", default=16)

    # args = parser.print_help()
