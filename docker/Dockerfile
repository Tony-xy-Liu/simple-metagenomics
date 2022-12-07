FROM condaforge/mambaforge

RUN mamba create --no-default-packages --yes \
    -n main -c bioconda \
    sra-tools megahit maxbin2 prodigal diamond snakemake

ADD load /app/
