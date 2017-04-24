#!/usr/bin/perl
use strict;
use Regexp::Assemble;
 
my $ra = Regexp::Assemble->new;
while (<>)
{
  $ra->add($_);
}
$_ = $ra->as_string();
s/([\x22\x27\x3b\x00-\x20\x7f-\xff])/sprintf "\\x%02x",ord($1)/eg;
print "$_\n"; 
