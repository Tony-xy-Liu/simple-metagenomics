rule all:
    input: f"{config['sample']}/diamond/done"

rule megahit:
    input:
        r1="{sample}/input/r1.fq",
        r2="{sample}/input/r2.fq",
    output: "{sample}/megahit/final.contigs.fa",
    threads: config["threads"],
    shell:
        """\
        megahit -t {threads} --no-mercy --k-list 31,59,87,115 \
            -1 {input.r1} \
            -2 {input.r2} \
            -o {wildcards.sample}/megahit/out \
        && ln -s {wildcards.sample}/megahit/out/final.contigs.fa {wildcards.sample}/megahit/final.contigs.fa
        """

rule maxbin2:
    input:
        r1="{sample}/input/r1.fq",
        r2="{sample}/input/r2.fq",
        asm="{sample}/megahit/final.contigs.fa"
    output: "{sample}/maxbin2/done",
    threads: config["threads"],
    shell:
        """\
        run_MaxBin.pl -thread {threads} -min_contig_length 2000 -max_iteration 30 \
            -reads {input.r1} -reads2 {input.r2} \
            -contig {input.asm} \
            -out {wildcards.sample}/maxbin2/ \
        && touch {wildcards.sample}/maxbin2/done
        """

rule prodigal:
    input: "{sample}/maxbin2/done",
    output: "{sample}/prodigal/done",
    shell:
        """\
        mkdir -p prodigal
        for bin in $(ls -a ./maxbin2 | grep .fasta); do
            prodigal \
                -i maxbin2/$bin \
                -a prodigal/$bin.faa
            if [ $? -ne 0 ]; then
                break
        done
        if [ $? -eq 0 ]; then
            touch {wildcards.sample}/prodigal/done
        """

rule diamond:
    input:
        prd="{sample}/prodigal/done",
        ref=config["cog"],
    output: "{sample}/diamond/done",
    threads: config["threads"],
    shell:
        """\
        mkdir -p diamond
        for bin in $(ls -a ./maxbin2 | grep .fasta); do
            diamond blastp \
                -p {threads} -f 6 qseqid stitle pident evalue \
                -d {input.ref} \
                -q prodigal/$bin.faa \
                -o diamond/$bin.tsv
            if [ $? -ne 0 ]; then
                break
        done
        if [ $? -eq 0 ]; then
            touch {wildcards.sample}/diamond/done
        """
