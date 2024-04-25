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

    #[structopt(short, long)]
    pub label: Option<String>,

    #[structopt(short = "c", long)]
    pub column: Option<usize>,

    //#[structopt(short, long, default_value = "0")]
    #[structopt(short, long)]
    pub hline: Option<Vec<usize>>,

    #[structopt(short = "s", long, default_value = "1.52")]
    pub scale: f64,
}

fn write_table(reader: &mut Reader<Stdin>, opt: &Opt) {
    let hline_set = match &opt.hline {
        Some(hline) => hline.iter().cloned().collect::<BTreeSet<usize>>(),
        None => BTreeSet::new(),
    };

    //let hline_set = opt.hline.iter().cloned().collect::<BTreeSet<usize>>();

    println!("\\begin{{table}}[{}]", &opt.table);
    if let Some(caption) = &opt.caption {
        println!("\\caption{{{}}}", caption);
    }
    if let Some(label) = &opt.label {
        println!("\\label{{{}}}", label);
    }

    let cols = opt.column.unwrap_or(reader.headers().unwrap().len());

    println!("\\renewcommand\\arraystretch{{{}}}", opt.scale);
    println!("\\centering");
    println!("\\begin{{tabular}}{{@{{}}{}@{{}}}}", "c".repeat(cols));
    println!("\\toprule");

    // consume headers
    if let Ok(result) = reader.headers() {
        let back = result.len() - 1;
        for record in result.iter().take(back) {
            print!("\\textbf{{{}}} & ", &record);
        }
        print!("\\textbf{{{}}} \\\\", &result.iter().last().unwrap());
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
            print!("\\bottomrule");
        }
        println!();
    }

    println!("\\bottomrule");
    println!("\\end{{tabular}}");
    println!("\\end{{table}}");
}
