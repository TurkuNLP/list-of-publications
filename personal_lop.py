import six
assert six.PY3, "Run me with python3"

import sys
import bibtexparser
import argparse
import collections

PType=collections.namedtuple("Ptype","label,bibtypes,section")

nocites="journal bookc conf phd coed techrep".split()
pub_types="article incollection inproceedings phdthesis proceedings techreport".split()  #can also be incollection,inbook


ptypes=[PType("journal",["article"],"Co-authored journal articles (OKM class A1)"),
        PType("bookc",["incollection"],"Co-authored peer-reviewed book chapters (OKM class A3)"),
        PType("conf",["inproceedings"],"Co-authored articles in peer-reviewed conference proceedings (OKM class A4)"),
        PType("techrep",["techreport"],"Co-authored technical reports (OKM class D4)"),
        PType("coed",["proceedings"],"Co-edited proceedings (OKM class C2)"),
        PType("phd",["phdthesis"],"PhD dissertation (OKM class G5)")]


preamble=r"""
\documentclass[a4paper,11pt]{article}
\usepackage{natbib}
\usepackage{multibib}
\usepackage{a4wide}
\pdfpagewidth=\paperwidth
\pdfpageheight=\paperheight

%\newcites{rel}{10 co-authored publications most relevant to the proposal (also repeated in their relevant category listing)}

%%%NEWCITESDEFS%%%

\title{List of publications}
\author{%%%LATEXAUTHOR%%%}

\begin{document}
\maketitle

%%%CITES%%%

%%%BIBSTYLES%%%

\end{document}
"""




parser = argparse.ArgumentParser(description='Generate a .tex which compiles into a personal publication list.')
parser.add_argument('--latexauthor', dest='latexauthor', nargs=1,help='The author field of the latex document, your name.',required=True)
parser.add_argument('-a','--author', dest='author', nargs="+",help='Space-separated strings to look for in the author E.g. --author Kanerva Nyblom',required=True)
parser.add_argument('-e','--editor', dest='editor', action='store_true',help='Also look in the editor field.')

args = parser.parse_args()
with open("turkunlp.bib") as f:
    db=bibtexparser.load(f)

matching={} #type -> [pubs]

for x in db.entries:
    for n in args.author:
        if n in x.get("author","") or (args.editor and n in x.get("editor","")):
            matching.setdefault(x["ENTRYTYPE"],[]).append(x)
            break

print("Found {} matching entries\n".format(sum(len(lst) for lst in matching.values())),file=sys.stderr)
for etype,lst in sorted(matching.items(),key=lambda etype_lst: len(etype_lst[1]), reverse=True):
    print("{:20} : {}".format(etype,len(matching[etype])),file=sys.stderr)


nocites="journal bookc conf phd coed techrep".split()
pub_types="article incollection inproceedings phdthesis proceedings techreport".split()  #can also be incollection,inbook

#\bibliographystylejournal{unsrtnat-nourl}
#\bibliographyjournal{turkunlp}

newcitedefs=[]
cites=[]
bibstyles=[]

for ptype in ptypes:
    records=[]
    for bib_type in ptype.bibtypes:
        records.extend(matching.get(bib_type,[]))
    for r in records:
        if "year" not in r:
            print("WARNING: record {} had no year".format(r["ID"]),file=sys.stderr)
            print(r,file=sys.stderr)

    records.sort(key=lambda rec:rec["year"],reverse=True)
    if records:
        #Found something
        newcitedefs.append(r"\newcites{{{}}}{{{}}}".format(ptype.label,ptype.section))

        bibstyles.append(r"\bibliographystyle{}{{unsrtnat-nourl}}\bibliography{}{{turkunlp}}".format(ptype.label,ptype.label))
        
        for r in records:
            cites.append(r"\nocite{}{{{}}} %%%{}".format(ptype.label,r["ID"],r["title"]))

p=preamble.replace("%%%NEWCITESDEFS%%%","\n".join(newcitedefs))
p=p.replace("%%%LATEXAUTHOR%%%",args.latexauthor[0])
p=p.replace("%%%CITES%%%","\n".join(cites))
p=p.replace("%%%BIBSTYLES%%%","\n".join(bibstyles))
print(p)
