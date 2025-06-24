# Ken::Url -- URL encoding and decoding

package Ken::Url;

use strict;

# statics

sub Unescape {
    my $str = shift;
    $str =~ tr/+/ /;
    $str =~ s/%([0-9a-f][0-9a-f])/chr hex $1/ieg;
    $str;
}

sub Escape {
    my $str = shift;
    $str =~ s/\W/$& eq ' ' ? '+' : sprintf '%%%02x', ord $&/eg;
    $str;
}

sub import { }

1;

