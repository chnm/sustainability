# Ken::Cgi -- CGI input decoding routines

package Ken::Cgi;

use strict;
use Ken::Url;

# check for mod_perl

my $mod_perl = $ENV{'GATEWAY_INTERFACE'} =~ /^CGI-Perl/;

# statics

sub SplitFields {
    my $hash = shift;
    foreach (split /&/, shift) {
        my ($a,$b) = map { Ken::Url::Unescape($_) } split(/=/, $_, 2);
        next if $a eq '';
        ($a,$b) = ('isindex',$a) if $b eq '';
        defined($hash->{$a}) ? ($hash->{$a}.="\0$b") : ($hash->{$a}=$b)
            if $a =~ /^\w+$/;
    }
    $hash;
}

sub GetFields {
    %ENV = Apache::request()->cgi_env if $mod_perl;
    my $ret = SplitFields {}, $main::ENV{'QUERY_STRING'};
    if ($main::ENV{'REQUEST_METHOD'} eq 'POST') {
        read STDIN, my $rawinput, $main::ENV{'CONTENT_LENGTH'};
        SplitFields $ret, $rawinput;
    }
    $ret;
}

my $mozilla = undef;
sub Mozilla {
    return $mozilla if defined($mozilla);
    my $agent = $ENV{'HTTP_USER_AGENT'};
    $mozilla = defined($agent) && ($agent =~ /mozilla/i);
}

sub Clean1 {
    my @ret = @_;
    for (@ret) {
	tr/ -~\200-\376//cd;
	s/^\s+//;
	s/\s+$//;
    }
    wantarray() ? @ret : $ret[0];
}

sub Clean {
    my @ret = @_;
    for (@ret) {
	tr/\n\r -~\200-\376//cd;
	s/\s+$//;
	s/\n\r|\r\n/\n/g;
	tr/\r/\n/;
    }
    wantarray() ? @ret : $ret[0];
}

sub import { }

1;

