# Ken::Pre -- <pre>..</pre> character escaping (for <, >, and &)

package Ken::Pre;

# statics

my %entity = (

	'lt'   => '<',
	'gt'   => '>',
	amp    => '&',
	quot   => '"',

	nbsp   => chr 160,
	iexcl  => chr 161,
	cent   => chr 162,
	pound  => chr 163,
	curren => chr 164,
	yen    => chr 165,
	brvbar => chr 166,
	sect   => chr 167,
	uml    => chr 168,
	copy   => chr 169,
	ordf   => chr 170,
	laquo  => chr 171,
	'not'  => chr 172,
	shy    => chr 173,
	reg    => chr 174,
	macr   => chr 175,
	deg    => chr 176,
	plusmn => chr 177,
	sup2   => chr 178,
	sup3   => chr 179,
	acute  => chr 180,
	micro  => chr 181,
	para   => chr 182,
	middot => chr 183,
	cedil  => chr 184,
	sup1   => chr 185,
	ordm   => chr 186,
	raquo  => chr 187,
	frac14 => chr 188,
	frac12 => chr 189,
	frac34 => chr 190,
	iquest => chr 191,
	Agrave => chr 192,
	Aacute => chr 193,
	Acirc  => chr 194,
	Atilde => chr 195,
	Auml   => chr 196,
	Aring  => chr 197,
	AElig  => chr 198,
	Ccedil => chr 199,
	Egrave => chr 200,
	Eacute => chr 201,
	Ecirc  => chr 202,
	Euml   => chr 203,
	Igrave => chr 204,
	Iacute => chr 205,
	Icirc  => chr 206,
	Iuml   => chr 207,
	ETH    => chr 208,
	Ntilde => chr 209,
	Ograve => chr 210,
	Oacute => chr 211,
	Ocirc  => chr 212,
	Otilde => chr 213,
	Ouml   => chr 214,
	'times'=> chr 215,
	Oslash => chr 216,
	Ugrave => chr 217,
	Uacute => chr 218,
	Ucirc  => chr 219,
	Uuml   => chr 220,
	Yacute => chr 221,
	THORN  => chr 222,
	szlig  => chr 223,
	agrave => chr 224,
	aacute => chr 225,
	acirc  => chr 226,
	atilde => chr 227,
	auml   => chr 228,
	aring  => chr 229,
	aelig  => chr 230,
	ccedil => chr 231,
	egrave => chr 232,
	eacute => chr 233,
	ecirc  => chr 234,
	euml   => chr 235,
	igrave => chr 236,
	iacute => chr 237,
	icirc  => chr 238,
	iuml   => chr 239,
	eth    => chr 240,
	ntilde => chr 241,
	ograve => chr 242,
	oacute => chr 243,
	ocirc  => chr 244,
	otilde => chr 245,
	ouml   => chr 246,
	divide => chr 247,
	oslash => chr 248,
	ugrave => chr 249,
	uacute => chr 250,
	ucirc  => chr 251,
	uuml   => chr 252,
	yacute => chr 253,
	thorn  => chr 254,
	yuml   => chr 255,
);

use strict;

sub Escape
{
    my $str = shift;
    $str =~ s/&/&amp;/g;
    $str =~ s/</&lt;/g;
    $str =~ s/>/&gt;/g;
    $str =~ s/"/&#34;/g;
    $str;
}

sub Unescape
{
	my @copy = @_;
	foreach (@copy)
	{
		s{ <!(.*?)(--.*?--\s*)+(.*?)> }{ if ($1 || $3) { "<!$1 $3>" } }gesx;
		s{ < (?: [^>'"]+ | ".*?" | '.*?')+ > }{}gsx;
		s{ ( &(?: \x23 (?:(\d+)|x([0-9a-f]+)) | (\w+) );? ) }
         { defined($2) ? chr($2) :
           defined($3) ? chr(hex($3)) : ($entity{$4} || $1) }gexi;
	}
	wantarray() ? @copy : $copy[0];
}

sub import { }

1;

