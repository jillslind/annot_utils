#! /usr/bin/env python

import gzip, subprocess
import chr_name, utils

def generate_edge_bed(ref_gene_file, output_file, chr_name_list):

    ucsc2new_chr = {}
    if chr_name_list is not None:
        with open(chr_name_list, 'r') as hin:
            for line in hin:
                F = line.rstrip('\n').split('\t')
                ucsc2new_chr[F[0]] = F[1]

    junction2annot = {}
    ##########
    # function for processing each line of refGene.txt.gz
    def proc_line(line, type):

        F  = line.rstrip('\n').split('\t')
        
        chr = ucsc2new_chr[F[2]] if F[2] in ucsc2new_chr else F[2]
        starts = F[9].split(',')
        ends = F[10].split(',')
        strand = F[3]
        exon_num = int(F[8])
        gene = F[1]
        symbol = F[12]

        chr = chr.replace("chr", "")
    
        for i in range(1, exon_num):
            
            key = chr + '\t' + starts[i] + '\t' + str(int(starts[i]) + 1) + '\t' + '-'
            annot = symbol + '(' + gene + ').' if type == "refGene" else gene
            annot = annot + (str(i) + ".start" if strand == '+' else str(exon_num - i) + ".end")
            if key in junction2annot: 
                junction2annot[key] = junction2annot[key] + ',' + annot
            else:
                junction2annot[key] = annot
        
    
        for i in range(0, exon_num - 1):
            
            key = chr + '\t' + str(int(ends[i]) - 1) + '\t' + ends[i] + '\t' + '+' 
            annot = symbol + '(' + gene + ').' if type == "refGene" else gene
            annot = symbol + '(' + gene + ').' + (str(i) + ".end" if strand == '+' else str(exon_num - i - 1) + ".start")
            
            if key in junction2annot: 
                junction2annot[key] = junction2annot[key] + ',' + annot
            else:
                junction2annot[key] = annot
    ##########

    with gzip.open(ref_gene_file, 'r') as hin:
        for line in hin:
            proc_line(line, "refGene")

    hout = open(output_file, 'w')
    for junction in sorted(junction2annot):
        junc_info = junction.split('\t')
        print >> hout, '\t'.join(junc_info[0:3]) + '\t' + junction2annot[junction] + '\t' + '0' + '\t' + junc_info[3]
    hout.close()


def broaden_edge(input_file, output_file, margin):

    hout = open(output_file, 'w')
    with open(input_file, 'r') as hin:
        for line in hin:
            F = line.rstrip('\n').split('\t')

            if (F[4] == "donor" and F[5] == '+') or (F[4] == "acceptor" and F[5] == '-'):
                print >> hout, F[0] + '\t' + str(int(F[1]) - margin + 1) + '\t' + str(int(F[2]) + margin) + '\t' + '\t'.join(F[3:])
            else:
                print >> hout, F[0] + '\t' + str(int(F[1]) - margin) + '\t' + str(int(F[2]) + margin - 1) + '\t' + '\t'.join(F[3:])

    hout.close()



def make_junction_info(output_file, genome_id, is_grc, donor_size, acceptor_size):


    # create UCSC to GRC chr name corresponding table
    ucsc2grc = {}
    if is_grc:
        ucsc2grc = chr_name.make_ucsc2grc(genome_id)

    ucsc_gene_file = utils.set_ucsc_gene_file(genome_id, "ref")


    donor_size_exon, donor_size_intron = [int(x) for x in donor_size.split(',')]
    acceptor_size_intron, acceptor_size_exon = [int(x) for x in acceptor_size.split(',')]

    key2junction, key2gene_id, key2exon_num = {}, {}, {}
    with gzip.open(ucsc_gene_file, 'r') as hin:
        for line in hin:
            F = line.rstrip('\n').split('\t')

            chr = ucsc2grc[F[2]] if F[2] in ucsc2grc else F[2] 
            starts = [int(x) for x in F[9].split(',') if x != '']
            ends = [int(x) for x in F[10].split(',') if x != '']
            strand = F[3]
            exon_num = int(F[8])
            gene_id = F[1]
            symbol = F[12]

            for i in range(0, exon_num - 1):
                if strand == '+': # donor
                    key = '\t'.join([chr, str(ends[i] - donor_size_exon), str(ends[i] + donor_size_intron), symbol, "donor", strand])
                else: # acceptor
                    key = '\t'.join([chr, str(ends[i] - acceptor_size_exon), str(ends[i] + acceptor_size_intron), symbol, "acceptor", strand])
                
                junction = chr + ':' + str(ends[i]) + '-' + str(starts[i + 1] + 1)

                if key not in key2junction: key2junction[key] = []
                if key not in key2gene_id: key2gene_id[key] = []
                if key not in key2exon_num: key2exon_num[key] = []

                key2junction[key].append(junction)
                key2gene_id[key].append(gene_id)
                key2exon_num[key].append(str(i))


            for i in range(1, exon_num):
                if strand == '+': # acceptor 
                    key = '\t'.join([chr, str(starts[i] - acceptor_size_intron), str(starts[i] + acceptor_size_exon), symbol, "acceptor", strand])
                else: # donor 
                    key = '\t'.join([chr, str(starts[i] - donor_size_intron), str(starts[i] + donor_size_exon), symbol, "donor", strand])

                junction = chr + ':' + str(ends[i - 1]) + '-' + str(int(starts[i]) + 1)

                if key not in key2junction: key2junction[key] = []
                if key not in key2gene_id: key2gene_id[key] = []
                if key not in key2exon_num: key2exon_num[key] = []
                
                key2junction[key].append(junction) 
                key2gene_id[key].append(gene_id) 
                key2exon_num[key].append(str(i)) 


    hout = open(output_file + ".unsorted.tmp", 'w')
    for key in sorted(key2junction):
        print >> hout, '\t'.join([key, ','.join(key2junction[key]), ','.join(key2gene_id[key]), ','.join(key2exon_num[key])])
    hout.close()

    hout = open(output_file + ".sorted.tmp", 'w')
    subprocess.call(["sort", "-k1,1", "-k2,2n", "-k3,3n", output_file + ".unsorted.tmp"], stdout = hout)
    hout.close()

    hout = open(output_file, 'w')
    subprocess.check_call(["bgzip", "-f", "-c", output_file + ".sorted.tmp"], stdout = hout)
    hout.close()

    subprocess.check_call(["tabix", "-p", "bed", output_file])

    subprocess.check_call(["rm", "-rf", output_file + ".unsorted.tmp"])
    subprocess.check_call(["rm", "-rf", output_file + ".sorted.tmp"])


