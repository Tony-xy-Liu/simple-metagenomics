# Simple Metagenomics
A BIOF501 term project for inferring protein annotations of metagenome-assembled genomes (MAG) from metagenomic reads hosted on [NCBI's sequence read archive (SRA)](https://www.ncbi.nlm.nih.gov/sra)

-------------------------

## For the Impatient
Setup:
```
pip install simple-metagenomics
smg setup -r ./ref
```
To run **with default subsampling** (to 1% of the original for improved runtime):
```
smg run -r ./ref -i SRR19573024 -o ./out
```
To run with **no subsampling**:
```
smg run -r ./ref -s 1 -i SRR19573024 -o ./out
```

## Background and Rationale

Throughout the various biomes of Earth, complex consortia of microorganisms thrive and cycle nutrients at scales ranging from symbiosis to global biogeochemical cycles. The study of these consortia has contributed to advances in many fields, including health in the context of host microbiomes [[1](#references)], renewable energy in the context of biofuels [[2](#references)], and ecology in the context of distributed metabolisms [[3](#references)]. Since only a select few microbes have been successfully cultured in laboratory conditions, the typical approach is to interrogate the microbial gene content of a sample directly using metagenomics.

The aim of this pipeline is to provide the simplest possible method for downloading and then converting raw metagenomic sequences into meaningful annotations. For additional details, please refer to the [implementation](#implementation) section.

## Usage

### **Manual Dependencies**

- Linux OS/amd64
- Python, version>=3.4 (so that you also have pip)
- Singularity

### **Installation**
We recommend that you use a virtual environment

via conda...<br>
[install miniconda](https://docs.conda.io/en/latest/miniconda.html)
```
conda create --no-default-packages --name smg python -y
conda activate smg
```

**or** via venv
```
pip install venv
python -m venv ./smg
source ./smg/bin/activate

```

In the environment, install simple metagenomics
```
pip install simple-metagenomics
```

Select a folder to save additional reference resources (`./ref`).
```
smg setup -r ./ref
```

### **Execution**

Obtain the SRA run ID for a whole genome metagenomics sequencing entry. For example, we use `SRR19573024`, which points to reads for a cyanobacteria bioreactor community [[4](#references)]. `./ref` refers to the same folder used in the last installation step.<br>
[Example search](https://www.ncbi.nlm.nih.gov/sra?term=(%22metagenome%22%5BOrganism%5D)%20AND%20%22wgs%22%5BStrategy%5D)

```
smg run -r ./ref -i SRR19573024 -o ./out
```

Once complete, look for annotation tables under `./out/SRR19573024/diamond/`.<br>
*Expected runtime: ~30 minutes with 16 threads and subsampled to 1%.*

Expected output:<br>

    ./out                       # base output path specified with "-o"
    ├── .snakemake              # snakemake generated files, including logs
    ├── snakemake               # snakemake cache
    ├── SRR19573024
        ├── sra_raw             # original fastqs from SRA
        ├── input               # subsampled fastqs
        ├── megahit             # intermediate metagenomic assembly
        ├── maxbin2             # intermediate bins
        ├── prodigal            # intermediate ORFs per bin
        ├── diamond
            ├── 001.fasta.tsv   # annotation table for 1 bin
            ├── 002.fasta.tsv   # 2 bins should be resolved from SRR19573024 by default

Columns: Query ID (ORF), Subject title (annotation), Percentage of identical matches, Expected value <br>
Interestingly, photosynthesis genes were found in both bins, including photosystems I and II. Bin 001, however, showed a greater potential to fix nitrogen since nifB, nifS, and nifU were identified which accounts for 3 out of the 4 genes of a known nitrogen fixation operon [[5](#references)]. While the remaining gene, fdxN, was not explicitly identified, a ferredoxin nitrite reductase was found in its' stead. Only nifB was found in bin 002.

[Complete annotation tables](https://github.com/Tony-xy-Liu/simple-metagenomics/tree/main/example_output)

## Implementation

<table>
 <tr>
    <td>
        <img src="https://raw.githubusercontent.com/Tony-xy-Liu/simple-metagenomics/main/resources/dag.svg" alt="(workflow diagram, view on github)" style="min-width:25vw;max-height:75vh" width="800px"/>
    </td>
    <td valign="top">
        <p>
            The workflow is managed by snakemake [<a href="#references">6</a>] with all workflow-related dependencies packaged into a Docker container to maximize reproducibiltiy. Due to its' rising popularity, especially in the research community, Singularity [<a href="#references">7</a>] may be used as an alternative to Docker. The container image is hosted on <a href="https://quay.io/repository/txyliu/simple-metagenomics">Quay.io</a> and automatically pulled during setup.
        </p>
        <p>
            <b>sra_download:</b> Using <a href="https://github.com/ncbi/sra-tools/wiki">sra toolkit</a>, we download the paired-paired end fastqs pointed to by the given SRA run ID.
        </p>
        <p>
            <b>subsample:</b> A python script randomly subsamples the fastq reads to the given percentage using <a href="https://numpy.org/doc/stable/">numpy</a>
        </p>
        <p>
            <b>Megahit [<a href="#references">8</a>]:</b> The subsampled reads are assembled into longer segments (contigs).
        </p>
        <p>
            <b>Maxbin2 [<a href="#references">9</a>]:</b> These segments are then clusted into bins based on tetranucleotide frequency and read coverage.
        </p>
        <p>
            <b>Prodigal [<a href="#references">10</a>]:</b> The contigs of each bin are then scanned for open reading frames (ORF) by using a dynamic programming algorithm that takes into account ribosomal binding sites, start & stop codons, and ORF length.
        </p>
        <p>
            <b>Diamond [<a href="#references">11</a>]:</b> Predicted ORFs are annotated based on the degree of homology with known reference sequences in the <b>Clusters of Orthologous Genes (COG)</b> [<a href="#references">12</a>] database.
        </p>
    </td>
 </tr>
</table>

## **Command Line Interface**
```
$ smg
simple-metagenomics v1.0
https://github.com/Tony-xy-Liu/simple-metagenomics

Syntax: smg COMMAND [OPTIONS]

Where COMMAND is one of:
setup
run

for additional help, use:
smg COMMAND -h
```
```
$ smg setup
usage: smg setup [-h] -r PATH [-c TYPE]

optional arguments:
  -h, --help  show this help message and exit
  -r PATH     where to save required resources
  -c TYPE     the resource container type, choose from: "singularity"
              (default) or "docker"

the following arguments are required: -r
```
```
$ smg run
usage: smg run [-h] -r PATH -i SRA_ID -o PATH [-s DECIMAL] [-t INT] [--mock]

optional arguments:
  -h, --help  show this help message and exit
  -r PATH     path to saved required resources from running: smg setup
  -i SRA_ID   example: SRR19573024
  -o PATH     output folder
  -s DECIMAL  subsample fraction for raw reads, set to 1 for no subsampling,
              default:0.01
  -t INT      threads, default:16
  --mock      dry run snakemake

the following arguments are required: -r, -i, -o
```

## References

[1] [Thomas S, Izard J, Walsh E, Batich K, Chongsathidkiet P, Clarke G, Sela DA, Muller AJ, Mullin JM, Albert K, Gilligan JP, DiGuilio K, Dilbarova R, Alexander W, Prendergast GC. 2017. The Host Microbiome Regulates and Maintains Human Health: A Primer and Perspective for Non-Microbiologists. Cancer Res 77:1783–1812.](https://doi.org/10.1158/0008-5472.CAN-16-2929)

[2] [Nozzi N, Oliver J, Atsumi S. 2013. Cyanobacteria as a Platform for Biofuel Production. Front Bioeng Biotechnol 1.](https://www.frontiersin.org/articles/10.3389/fbioe.2013.00007/full)

[3] [McCutcheon JP, von Dohlen CD. 2011. An interdependent metabolic patchwork in the nested symbiosis of mealybugs. Curr Biol CB 21:1366–1372.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3169327/)

[4] [Noonan AJC, Qiu Y, Kieft B, Formby S, Liu T, Dofher K, Koch M, Hallam SJ. 2022. Metagenome-Assembled Genomes for “Candidatus Phormidium sp. Strain AB48” and Co-occurring Microorganisms from an Industrial Photobioreactor Environment. Microbiol Resour Announc 0:e00447-22.](https://doi.org/10.1128/mra.00447-22)

[5] [Mulligan ME, Haselkorn R. 1989. Nitrogen fixation (nif) genes of the cyanobacterium Anabaena species strain PCC 7120. J Biol Chem 264:19200–19207.](https://doi.org/10.1016/S0021-9258(19)47287-6)

[6] [Mölder F, Jablonski KP, Letcher B, Hall MB, Tomkins-Tinch CH, Sochat V, Forster J, Lee S, Twardziok SO, Kanitz A, Wilm A, Holtgrewe M, Rahmann S, Nahnsen S, Köster J. 2021. Sustainable data analysis with Snakemake. 10:33.](https://doi.org/10.12688/f1000research.29032.2)

[7] [Kurtzer GM, Sochat V, Bauer MW. 2017. Singularity: Scientific containers for mobility of compute. PLOS ONE 12:e0177459.](https://doi.org/10.1371/journal.pone.0177459)

[8] [Li D, Liu C-M, Luo R, Sadakane K, Lam T-W. 2015. MEGAHIT: an ultra-fast single-node solution for large and complex metagenomics assembly via succinct de Bruijn graph. Bioinformatics 31:1674–1676.](https://doi.org/10.1093/bioinformatics/btv033)

[9] [Wu Y-W, Simmons BA, Singer SW. 2016. MaxBin 2.0: an automated binning algorithm to recover genomes from multiple metagenomic datasets. Bioinformatics 32:605–607.](https://doi.org/10.1093/bioinformatics/btv638)

[10] [Hyatt D, Chen G-L, LoCascio PF, Land ML, Larimer FW, Hauser LJ. 2010. Prodigal: prokaryotic gene recognition and translation initiation site identification. BMC Bioinformatics 11:119.](https://doi.org/10.1186/1471-2105-11-119)

[11] [Buchfink B, Xie C, Huson DH. 2015. Fast and sensitive protein alignment using DIAMOND. 1. Nat Methods 12:59–60.](https://doi.org/10.1038/nmeth.3176)

[12] [Tatusov RL, Galperin MY, Natale DA, Koonin EV. 2000. The COG database: a tool for genome-scale analysis of protein functions and evolution. Nucleic Acids Res 28:33–36.](https://doi.org/10.1093%2Fnar%2F28.1.33)
