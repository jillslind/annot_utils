#! /usr/bin/env python

import sys, gzip, subprocess, pkg_resources 
import chr_name, utils

def make_simple_repeat_info(output_file, genome_id, is_grc):

    # create UCSC to GRC chr name corresponding table
    ucsc2grc = {} 
    if is_grc:
        ucsc2grc = chr_name.make_ucsc2grc(genome_id)

    if genome_id == "hg19":
        simple_repeat_file = pkg_resources.resource_filename("annot_utils", "data/hg19/simpleRepeat.txt.gz")
    elif genome_id == "hg38":
        simple_repeat_file = pkg_resources.resource_filename("annot_utils", "data/hg38/simpleRepeat.txt.gz")
    elif genome_id == "mm10":
        simple_repeat_file = pkg_resources.resource_filename("annot_utils", "data/mm10/simpleRepeat.txt.gz")
    else:
        print >> sys.stderr, "genome_id shoud be hg19, hg38 or mm10"
        sys.exit(1)

    hout = open(output_file + ".unsorted.tmp", 'w')
    with gzip.open(simple_repeat_file, 'r') as hin:

        for line in hin:

            F = line.rstrip('\n').split('\t')
        
            chr = ucsc2grc[F[1]] if F[1] in ucsc2grc else F[1]
            print >> hout, chr + '\t' + '\t'.join(F[2:])

    hout.close()


    hout = open(output_file + ".sorted.tmp", 'w')
    subprocess.check_call(["sort", "-k1,1", "-k2,2n", "-k3,3n", output_file + ".unsorted.tmp"], stdout = hout)
    hout.close()

    hout = open(output_file, 'w')
    subprocess.check_call(["bgzip", "-f", "-c", output_file + ".sorted.tmp"], stdout = hout)
    hout.close()

    subprocess.check_call(["tabix", "-p", "bed", output_file])


    subprocess.check_call(["rm", "-rf", output_file + ".unsorted.tmp"])
    subprocess.check_call(["rm", "-rf", output_file + ".sorted.tmp"])


