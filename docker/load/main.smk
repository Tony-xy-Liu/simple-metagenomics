rule all:
    input: f"{config['sample']}/diamond/done"

rule sra_download:
    output:
        r1="{sample}/sra_raw/{sample}_1.fastq",
        r2="{sample}/sra_raw/{sample}_2.fastq",
    threads: config["threads"],
    shell:
        """\
        prefetch {wildcards.sample} -O {wildcards.sample}/sra_raw \
        && fasterq-dump --threads {threads} {wildcards.sample}/sra_raw/{wildcards.sample} -O {wildcards.sample}/sra_raw \
        """

rule subsample:
    input: "{sample}/sra_raw/{sample}_{n}.fastq"
    output: "{sample}/input/r{n}.ss.fq"
    shell:
        """\
        python /app/subsample.py {input} %s {output}
        """ % (config['ss'],)
    
rule megahit:
    input:
        r1="{sample}/input/r1.ss.fq",
        r2="{sample}/input/r2.ss.fq",
    output: "{sample}/megahit/final.contigs.fa",
    threads: config["threads"],
    shell:
        """\
        megahit -t {threads} --no-mercy --k-list 31,59,87,115 \
            -1 {input.r1} \
            -2 {input.r2} \
            -o {wildcards.sample}/megahit/out \
        && ln -s ./out/final.contigs.fa {wildcards.sample}/megahit/final.contigs.fa
        """
        
rule maxbin2:
    input:
        r1="{sample}/input/r1.ss.fq",
        r2="{sample}/input/r2.ss.fq",
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
        echo ls
        for bin in $(ls -a {wildcards.sample}/maxbin2 | grep .fasta); do
            prodigal \
                -i {wildcards.sample}/maxbin2/$bin \
                -a {wildcards.sample}/prodigal/$bin.faa
            result=$?
            if [ $result -ne 0 ]; then
                break
            fi
        done
        if [ $result -eq 0 ]; then
            touch {wildcards.sample}/prodigal/done
        fi
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
        for bin in $(ls -a {wildcards.sample}/maxbin2 | grep .fasta); do
            diamond blastp \
                -p {threads} -f 6 qseqid stitle pident evalue \
                -d {input.ref} \
                -q {wildcards.sample}/prodigal/$bin.faa \
                -o {wildcards.sample}/diamond/$bin.tsv
            result=$?
            if [ $result -ne 0 ]; then
                break
            fi
        done
        if [ $result -eq 0 ]; then
            touch {wildcards.sample}/diamond/done
        fi
        """
