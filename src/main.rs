
use regex::Regex;
use statrs::statistics::{Data, Max, Min, Statistics};
use std::fs::File;
use std::io::{self, BufRead};
use statrs::statistics::Distribution;
use plotters::prelude::*;
use std::path::PathBuf;

fn create_offset_plot(data: &Vec<f64>, device_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    create_plot(data, device_name, "Offset")
}

fn create_delay_plot(data: &Vec<f64>, device_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    create_plot(data, device_name, "Delay")
}

fn create_plot(data: &Vec<f64>, device_name: &str, plot_type: &str) -> Result<(), Box<dyn std::error::Error>> {
    let filename = format!("plots/{}-{}.png", device_name, plot_type).to_lowercase();
    let root = BitMapBackend::new(&filename, (640, 480)).into_drawing_area();
    root.fill(&WHITE)?;

    let max_value = data.max();
    let min_value = data.min();

    let mut chart = ChartBuilder::on(&root)
        .caption(format!("{} {}", device_name, plot_type), ("sans-serif", 30))
        .margin(20)
        .x_label_area_size(30)
        .y_label_area_size(70)
        .build_cartesian_2d(0..data.len(), min_value..max_value)?;

    chart.configure_mesh().x_desc("Sample Number").y_desc("Value (nanoseconds)").draw()?;

    chart.draw_series(LineSeries::new(
        data.iter().enumerate().map(|(x, y)| (x, *y)),
        &RED,
    ))?;

    Ok(())
}


fn parse_file(path: PathBuf, name: &str) -> io::Result<()> {
    let file = File::open(path)?;
    let reader = io::BufReader::new(file);

    let re = Regex::new(
            r#"(?x)
            ^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2})\s+
            \w+\s+
            ptp4l

        \[\d+\]

        :\s+
            ptp4l

        \[(?P<internal_ts>\d+\.\d+)\]

        :\s+
            master\s+offset\s+(?P<offset>[+-]?\d+)\s+s\d\s+
            freq\s+(?P<freq>[+-]?\d+)\s+
            path\s+delay\s+(?P<delay>[+-]?\d+)
            "#
        ).unwrap();

    let mut offsets = Vec::new();
    let mut delays = Vec::new();

    for line in reader.lines() {
        let line = line?;
        if let Some(cap) = re.captures(&line) {
            let offset: f64 = cap["offset"].parse().unwrap();
            let delay: f64 = cap["delay"].parse().unwrap();
            offsets.push(offset);
            delays.push(delay);
        }
    }

    if !offsets.is_empty() && !delays.is_empty() {
        let offset_data = Data::new(offsets.clone());
        let delay_data = Data::new(delays.clone());

        println!("\tOffset Stats:");
        println!("\t  Mean: {:.2}", offset_data.mean().unwrap());
        println!("\t  Min: {:.2}", offset_data.min());
        println!("\t  Max: {:.2}", offset_data.max());
        println!("\t  Std Dev: {:.2}", offset_data.std_dev().unwrap());
        let _ = create_offset_plot(&offsets, name);

        println!("\n\tDelay Stats:");
        println!("\t  Mean: {:.2}", delay_data.mean().unwrap());
        println!("\t  Min: {:.2}", delay_data.min());
        println!("\t  Max: {:.2}", delay_data.max());
        println!("\t  Std Dev: {:.2}", delay_data.std_dev().unwrap());
        let _ = create_delay_plot(&delays, name);
        return Ok(());
    } else {
        println!("No valid offset or delay data found.");
    }

    Ok(())
}
fn main() {

    let base_path = "/home/agebhard/Documents/repos/ptp-stats/data";

    let machines = [
        ("Beta", PathBuf::from(base_path).join("beta.log")),
        ("Charlie", PathBuf::from(base_path).join("charlie.log")),
        ("Delta", PathBuf::from(base_path).join("delta.log")),
        ("Echo", PathBuf::from(base_path).join("echo.log")),
    ];

    for (name, path) in machines {
        println!("{}", name);

        let status = parse_file(path, name);
        match status {
            Ok(_) => { println!(""); }
            Err(err) => { println!("[{}] Error: {:?}", name, err) }
        }
    }
}
