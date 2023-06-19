import pandas as pd
import logging
import math

columns = ["seqid","qlen","length","pident","mismatch","qstart","qend",
            "sstart","send","gaps","evalue","taxonomy", "dbseqid"]

logging.basicConfig(filename=str(snakemake.log),
            level=logging.DEBUG)

blast_df = pd.read_csv(snakemake.input["blast_result"], sep="\t",names=columns, index_col="seqid")
blast_df = blast_df.drop(['taxonomy'], axis=1)

taxids = list(set(blast_df["dbseqid"]))

tax_df = pd.read_hdf(snakemake.input["lineage"], 'df')
tax_df = tax_df.loc[taxids, :]


def create_filter_set():
    res_set = set()
    for f in snakemake.params.drop_tax_classes.split(","):
        f = f.strip()
        if any(tax_df.index == f):
            res_set.add(f)
        else:
            tmp = tax_df[tax_df.taxonomy.str.contains(f, na=False)]
            res_set.update(tmp.index)
    return res_set


querynames=list(set(blast_df.index.values))

header = True
f_set = create_filter_set()
for i in querynames:
    blast_res = blast_df.loc[i,:] # blast results
    if blast_res.ndim == 1: # case only 1 blast hit
        blast_res = blast_res.to_frame().T
    blast_res = blast_res[~blast_res['dbseqid'].isin(f_set)] # remove blast results with blacklisted taxonomy
    if blast_res.empty:
        continue
    tax_res = tax_df.loc[blast_res['dbseqid'],:] # taxonomy for result
    tax_res = tax_res.set_index(blast_res.index)
    blast_res = pd.concat([blast_res, tax_res], axis=1)
    mode = 'w' if header else 'a'
    best_tax = blast_res[["qlen","length","pident","mismatch","qstart","qend", "sstart","send","gaps","evalue","taxonomy"]]
    best_tax.to_csv(snakemake.output[0], mode=mode, header=header, sep="\t", index=True, index_label="seqid")
    header = False
