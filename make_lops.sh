function make_lop {
    dirname=$1
    author=$2
    shift
    shift
    echo $author
    rm -rf $dirname
    mkdir $dirname
    python3 personal_lop.py --latex "$author" --author $* -e > $dirname/$dirname.tex
    cd $dirname
    ln -s ../turkunlp.bib .
    ln -s ../unsrtnat-nourl.bst .
    pdflatex $dirname.tex
    for a in *.aux
    do
	bibtex $a
    done
    pdflatex $dirname.tex
    pdflatex $dirname.tex
    cd ..
    echo
    echo
}

#       directory  latexname   search
make_lop ginter "Filip Ginter" Ginter
make_lop kanerva "Jenna Kanerva (Nyblom)" Kanerva Nyblom
make_lop mehryary "Farrokh Mehryary" Mehryary
make_lop luotolahti "Juhani Luotolahti" Luotolahti





