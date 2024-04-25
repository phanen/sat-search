#!/usr/bin/env rust-script
//! ```cargo
//! [dependencies]
//! structopt = { version = "0.3", features = [ "paw" ] }
//! paw = "1.0"
//! csv = "1.1"
//! ```
use csv::Reader;
use std::collections::BTreeSet;
use std::{io, io::Stdin};
use structopt::{clap, StructOpt};

fn main() {
    let opt = Opt::from_args();

    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .from_reader(io::stdin());

    write_table(&mut reader, &opt);
}

#[derive(Debug, StructOpt)]
#[structopt(name = "csv2tbl")]
#[structopt(setting(clap::AppSettings::ColoredHelp))]
pub struct Opt {
    #[structopt(short, long, default_value = "H")]
    pub table: String,

    #[structopt(short = "C", long)]
    pub caption: Option<String>,

    #[structopt(long)]
    pub caption_is_under: bool,

    #[structopt(short, long)]
    pub label: Option<String>,

    #[structopt(short, long)]
    pub column: Option<usize>,

    #[structopt(short, long, default_value = "0")]
    pub hline: Vec<usize>,
}

fn write_table(reader: &mut Reader<Stdin>, opt: &Opt) {
    let hline_set = opt.hline.iter().cloned().collect::<BTreeSet<usize>>();

    println!("\\begin{{table}}[{}]", &opt.table);
    if !opt.caption_is_under {
        if let Some(caption) = &opt.caption {
            println!("\t\\caption{{{}}}", caption);
        }
    }
    if let Some(label) = &opt.label {
        println!("\t\\label{{{}}}", label);
    }

    let cols = opt.column.unwrap_or(reader.headers().unwrap().len());

    println!("\\renewcommand\\arraystretch{{1.52}}");
    println!("\\centering");

    println!("\\begin{{tabular}}{{@{{}}{}@{{}}}}", "c".repeat(cols));
    println!("\\toprule");

    // consume headers
    if let Ok(result) = reader.headers() {
        for i in 0..cols - 1 {
            print!("\\textbf{{{}}} & ", &result[i]);
        }
        print!("\\textbf{{{}}} \\\\", &result[cols - 1]);
        print!(" \\midrule");
        println!();
    }

    for (i, result) in reader.records().enumerate() {
        // TODO: better to use a transformer
        let record = result.unwrap();
        let back = record.len() - 1;
        for i in 0..back {
            if i == 0 {
                print!("\\textbf{{{}}} & ", &record[i]);
            } else {
                print!("${}$ & ", &record[i]);
            }
        }
        print!("${}$ \\\\", &record[back]);
        if hline_set.contains(&(i + 1)) {
            print!(" \\bottomrule");
        }
        println!();
    }

    println!("\t\\bottomrule");
    println!("\t\\end{{tabular}}");
    if opt.caption_is_under {
        if let Some(caption) = &opt.caption {
            println!("\t\\caption{{{}}}", caption);
        }
    }
    println!("\\end{{table}}");
}
