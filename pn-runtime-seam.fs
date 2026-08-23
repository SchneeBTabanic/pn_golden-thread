\ pn-runtime-seam.fs — caller-owned entry words for run.py.
\ Lives in pn_golden-thread, not in the scribe. No flags, no help, no parser.
\ Operands after `--` via next-arg. Bodies on stdin. Nothing user-supplied
\ is interpolated into source.
\
\ The caller (run.py) loads the leaves from cwd = pn_gf-scribe-wb:
\   gforth pn-keep.fs pn-gread.fs pn-gindex.fs THIS-FILE -e 'WORD bye' -- args
\ Do NOT load pn_gf-scribe.fs: its greeting would land on stdout.
\ This file is entry words only. No require — require would look beside
\ this file, not in the scribe.

\ --- argv after `--` -------------------------------------------------------
\ next-arg at the prompt is compile-only; these words are colon defs.
: seam-arg ( -- a u )
   next-arg
   2dup s" --" compare 0= if 2drop next-arg then ;

create seam-pile 1024 allot  variable seam-pile#
create seam-tags 512 allot   variable seam-tags#
create seam-key  64 allot    variable seam-key#
create seam-val 256 allot    variable seam-val#
create seam-join 256 allot   variable seam-join#
variable seam-first?

\ stdin as a body xt. keep redirects outfile to the pile; stdin stays stdin.
: .stdin-body ( -- )
   begin  pad 1024 stdin read-file throw  dup
   while  pad swap type
   repeat drop ;

: (.kept) ( -- )
   ." pn-scribe: KEPT "
   seam-pile seam-pile# @ g-genesis
   dup GENESIS-DECLARED = if
      drop type
   else
      2drop drop ." UNLINKABLE"
   then
   ." #" keep-off @ 0 .r ." /"
   keep-formed 2@ <# #s #> type cr ;

: .kept-line ( -- )
   stderr ['] (.kept) with-output-to ;

: keep-stdin ( -- )
   seam-arg  seam-pile 1024 >fixed seam-pile# !
   seam-arg  seam-tags 512  >fixed seam-tags# !
   ['] .stdin-body  seam-tags seam-tags# @  seam-pile seam-pile# @  keep
   .kept-line ;

\ --- export-bare: bodies only, caller joiner --------------------------------
\ Nearest existing word is g-view (headers + banners). This is the gap.
variable se-hit?

: /sel ( a u -- )
   2dup [char] : scan dup 0= abort" pn-scribe: REFUSED — selector is not key:value"
   1 /string 2>r                    ( a u ) ( R: va vu )
   2r@ nip 1+ -                     ( a ku )
   seam-key 64 >fixed seam-key# !
   2r> seam-val 256 >fixed seam-val# ! ;

: (se-match) ( ka ku va vu -- )
   2>r  seam-key seam-key# @ compare 0= if
      2r@ seam-val seam-val# @ compare 0= if true se-hit? ! then
   then  2r> 2drop ;

: export-bare ( -- )
   seam-arg  seam-pile 1024 >fixed seam-pile# !
   seam-arg  /sel
   seam-arg  seam-join 256 >fixed seam-join# !
   true seam-first? !
   seam-pile seam-pile# @ g-open  0 g-to
   begin g-line while
      2dup g-hdr? if
         false se-hit? !
         2dup ['] (se-match) g-each-tag
         se-hit? @ if
            seam-first? @ 0= if seam-join seam-join# @ type then
            false seam-first? !
            2dup g-extent g-emit-body
         else
            2dup g-extent g-past-body
         then
      then 2drop
   repeat 2drop g-close ;

: toc-by ( -- )
   seam-arg  seam-arg  g-toc ;

: keys-of ( -- )
   seam-arg  g-keys ;
