import sys
import re
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

# A1, A3, A4. The summary sentence counts only these.
peer_reviewed_labels={"journal","bookc","conf"}

# bib field collab = "nat" (national, across institutes) or "int" (international)
def field_value(rec, key, default=""):
    # bibtexparser 2: entry.get returns a Field; entry[key] returns the value
    try:
        v=rec[key]
    except KeyError:
        return default
    if v is None:
        return default
    return v

def collab_key(rec):
    v=str(field_value(rec,"collab")).strip().lower()
    if v in ("nat","int"):
        return v
    if v:
        return v #unexpected value, keep it visible in the stats
    return "unmarked"

def collab_counts(records):
    return collections.Counter(collab_key(r) for r in records)

def format_collab(c):
    bits=["nat: {:3}".format(c["nat"]), "int: {:3}".format(c["int"]), "unmarked: {:3}".format(c["unmarked"])]
    for k in sorted(c):
        if k not in ("nat","int","unmarked"):
            bits.append("{}: {:3}".format(k,c[k]))
    return "  ".join(bits)

def author_parts(author):
    return [p.strip() for p in re.split(r"\s+and\s+", author.strip()) if p.strip()]

def firstauthor_positions(rec):
    # firstauthor="1,2" : those 1-based positions share first authorship
    raw=str(field_value(rec,"firstauthor")).strip()
    positions=set()
    for part in raw.split(","):
        part=part.strip()
        if not part:
            continue
        if part.isdigit():
            positions.add(int(part))
        else:
            print("WARNING: record {} has unreadable firstauthor value {!r}".format(rec["ID"],raw),file=sys.stderr)
    return positions

def is_first_or_shared(rec, needles):
    # position 1, or a later position listed in firstauthor
    author=str(field_value(rec,"author"))
    if not author:
        return False
    shared=firstauthor_positions(rec)
    for i,name in enumerate(author_parts(author), start=1):
        if any(n in name for n in needles) and (i==1 or i in shared):
            return True
    return False

def format_type_stats(records, needles):
    n_first=sum(1 for r in records if is_first_or_shared(r, needles))
    return "first: {:3}   {}".format(n_first, format_collab(collab_counts(records)))

def stats_line(label, records, needles):
    return "{:20} : {:4}   {}".format(label, len(records), format_type_stats(records, needles))

def eqcontrib_block(names):
    # .bst appends \eqcontrib{Surname} for every firstauthor position.
    # Star only the surnames passed with --author.
    lines=[
        "% Shared first authorship: the .bst emits \\eqcontrib{Surname} after every",
        "% author listed in a bib entry's firstauthor field. Star only the surnames",
        "% named here; everyone else gets nothing.",
        r"\newcommand{\eqcontrib}[1]{%",
        r"  \ifnum0%",
    ]
    for name in names:
        lines.append(r"    \ifnum\pdfstrcmp{\detokenize{#1}}{"+name+r"}=0 1\fi")
    lines.append(r"    >0 \textsuperscript{*}\fi}")
    return "\n".join(lines)


preamble=r"""
\documentclass[a4paper,11pt]{article}
\usepackage{natbib}
\usepackage{multibib}
\usepackage{a4wide}
\pdfpagewidth=\paperwidth
\pdfpageheight=\paperheight



%%%NEWCITESDEFS%%%

\title{List of publications}
\author{%%%LATEXAUTHOR%%%}

\begin{document}
\maketitle

%%%SUMMARY%%%

\noindent\textsuperscript{*}\,Shared first authorship.


%%%CITES%%%

%%%BIBSTYLES%%%

\end{document}
"""




parser = argparse.ArgumentParser(description='Generate a .tex which compiles into a personal publication list.')
parser.add_argument('--latexauthor', dest='latexauthor', nargs=1,help='The author field of the latex document, your name.',required=True)
parser.add_argument('-a','--author', dest='author', nargs="+",help='Space-separated strings to look for in the author E.g. --author Kanerva Nyblom',required=True)
parser.add_argument('-e','--editor', dest='editor', action='store_true',help='Also look in the editor field.')
parser.add_argument('-r','--relevant', dest='relevant', default="", nargs=1, help='Comma-separated (no space) list of bibids to produce the related citations part, if any')
parser.add_argument('-y','--year-since', dest='year', default=1800, nargs=1, type=int,  help='Only publications whose year is greater or equal to this')

args = parser.parse_args()
# v2 replaced bibtexparser.load; NormalizeFieldKeys keeps author/year/collab lowercase
db=bibtexparser.parse_file(
    "turkunlp.bib",
    append_middleware=[bibtexparser.middlewares.NormalizeFieldKeys()],
)
if db.failed_blocks:
    print("WARNING: {} bib blocks failed to parse".format(len(db.failed_blocks)),file=sys.stderr)
    for b in db.failed_blocks:
        print("  line {}: {}".format(b.start_line,b.error),file=sys.stderr)

matching={} #type -> [pubs]

for x in db.entries:
    #whih year?
    y=str(x["year"]).split()[0] #sometimes these go like "2018 (to appear)"
    y=int(y)
    if y<args.year:
        continue
    for n in args.author:
        if n in str(field_value(x,"author")) or (args.editor and n in str(field_value(x,"editor"))):
            matching.setdefault(x["ENTRYTYPE"].lower(),[]).append(x)
            break

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

if args.relevant:
    bibstyles.insert(0,r"\bibliographystyle{}{{unsrtnat-nourl}}\bibliography{}{{turkunlp}}".format("rel","rel"))
    newcitedefs.insert(0,r"\newcites{rel}{Co-authored publications most relevant to the proposal (also repeated in their relevant category listing)}")
    for x in args.relevant[0].split(",")[::-1]:
        cites.insert(0,r"\nociterel{{{}}}".format(x))
            
rows=[] # (label, records) in publication-type order
covered=set()
for ptype in ptypes:
    records=[]
    for bib_type in ptype.bibtypes:
        records.extend(matching.get(bib_type,[]))
        covered.add(bib_type)
    if records:
        rows.append((ptype.label, records))
for etype,lst in sorted(matching.items(),key=lambda etype_lst: len(etype_lst[1]), reverse=True):
    if etype not in covered and lst:
        rows.append((etype, lst))

all_records=[r for lst in matching.values() for r in lst]
peer=[r for label,lst in rows if label in peer_reviewed_labels for r in lst]
n_journal=sum(len(lst) for label,lst in rows if label=="journal")
n_first=sum(1 for r in peer if is_first_or_shared(r, args.author))
peer_collab=collab_counts(peer)
sentence=("% \\noindent Total of {} peer-reviewed publications. "
          "% Of these {} first or shared-first authorship, {} national collaboration, "
          "% and {} international collaboration.").format(
              len(peer), n_first, peer_collab["nat"], peer_collab["int"])

stat_lines=["Found {} matching entries".format(len(all_records))]
stat_lines.append("Collaboration: {}".format(format_collab(collab_counts(all_records))))
stat_lines.append("")
for label,records in rows:
    stat_lines.append(stats_line(label, records, args.author))
stat_lines.append("")
stat_lines.append(stats_line("peer-reviewed", peer, args.author))
stat_lines.append(stats_line("all", all_records, args.author))
commented="\n".join("% "+line if line else "%" for line in stat_lines)

p=preamble.replace("%%%NEWCITESDEFS%%%",eqcontrib_block(args.author)+"\n\n"+"\n".join(newcitedefs))
p=p.replace("%%%LATEXAUTHOR%%%",args.latexauthor[0])
p=p.replace("%%%SUMMARY%%%",sentence+"\n\n"+commented)
p=p.replace("%%%CITES%%%","\n".join(cites))
p=p.replace("%%%BIBSTYLES%%%","\n".join(bibstyles))
print(p)

for line in stat_lines:
    print(line,file=sys.stderr)
