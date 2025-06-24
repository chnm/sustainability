#!/usr/bin/perl
# yourTranscription.cgi
# January 28, 2000 andy@miranda.org

# This script takes the form input from tryTranscripting.html (which
# should reside in the same dir), replaces the placeholders in the template
# with the appropriate values, and then outputs the results as an HTML page. 

# It expects the template page placeholders to look like this:
#	<!--A1-->
# If there isn't a form value/placeholder match, it moves on to the next value.


### tweak the next 3 variables for your server: 
#
	# If it's not in the same directory as this script, use an absolute path.
	$page_template = "yourTranscription_template";

	# If you don't want to send the webmaster an email if something fails,
	# comment out the $mailprog and $webmaster lines:
	$mailprog = "/usr/lib/sendmail";        	# this needs to be the correct path
	$webmaster = "webmaster\@dohistory.org";        # note \@ instead of @
#
### end variables; nothing more needs to be customized




## Read the template file, die if unable.
        open PAGE, "$page_template" or &error('Cannot open template file');
	flock(PAGE, 2) or &error('Cannot lock template file'); 
	@page = <PAGE>;
	$page = join("",@page);
	close PAGE;

## Reads & sanitizes form data in POST format.
	if ($ENV{'REQUEST_METHOD'} eq 'POST') {
        	# Get the input
        	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
         	# Split the name-value pairs
        	@pairs = split(/&/, $buffer);
	} else {
		# No form data, perhaps the user tried to look at the cgi page directly.
		# Redirect to back tryTranscribing.html
		print "Location: tryTranscribing.html","\n\n";
		die;
	} 

## For each name-value pair:                                             
	foreach $pair (@pairs) {
		# Split the pair up into individual variables.                      
		local($name, $value) = split(/=/, $pair);

		# Decode the form encoding on the value variables.          
		$value =~ tr/+/ /;
		$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

		# Explicitly removes server side includes if someone attempts to insert one.
		$value =~ s/<!--(.|\n)*-->//g;
		# Removes null characters.
		$value =~ s/\0//g;
		# Removes HTML formatting.
		$value =~ s/<([^>]|\n)*>//g;
		# Replaces & and " 
		$value =~ s/\&/\&amp\;/g;
		$value =~ s/"/\&quot\;/g;
   
		# The clincher: swaps values for placeholders in template file		
                $page =~ s/<!--($name)-->/$value/si;
		}

## Everything ostensibly went ok, so the resulting page is output.  
        print "Content-type: text/html\n\n";
	print $page;

## ...and that's it. Fini.


## The error subroutine. 
	sub error{
		my $error = shift;
		## Redirect to tryTranscribing.html.    
                print "Location: tryTranscribing.html","\n\n";
		# Send an apologetic note to the webmaster
		if ($webmaster) {
			my $now = `date`;
			open MAIL, "|$mailprog -t" or die;
			print MAIL <<END;
To: $webmaster
From: yourTranscription.cgi
Subject: ERROR generating yourTranscription page

At $now 
the $0 script, which accepts form data from tryTranscribing.html
died with this message: $error

PERL's error message: $!

The user was redirected to tryTranscribing.html.
Sorry.

END
			close MAIL;
			die;
		}
	}

	exit(0);
