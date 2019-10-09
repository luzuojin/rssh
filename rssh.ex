#!/usr/bin/expect
set dir [file dirname [info script]]

set alias_nx [lindex $argv 0]
append alias_nx " not exists"

set out [exec python $dir/rssh.py show $argv]

if {$out == $alias_nx} {
    puts $out
} else {
    set params [split $out "\t"]
    set alias [lindex $params 0]
    set user [lindex $params 1]
    set host [lindex $params 2]
    set port [lindex $params 3]
    set pass [lindex $params 4]
    set term $env(TERM)

    # set title
    set env(TERM) "vt100"
    puts "\033]0;$alias ~ $user@$host\007"

    # ssh remote
    set timeout 30
    spawn ssh $user@$host -p$port -o TCPKeepAlive=yes -o ServerAliveInterval=30
    expect {
            "(yes/no)?"
            {send "yes\n";exp_continue}
            "assword:"
            {send "$pass\n"}
    }
    interact

    # reset title
    set env(TERM) $term
}

