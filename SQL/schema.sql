CREATE TABLE earnings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10),
    fiscal_date_ending DATE,
    reported_date DATE,
    reported_eps FLOAT,
    estimated_eps FLOAT,
    surprise FLOAT,
    surprise_percentage FLOAT,
    report_time VARCHAR(20)
);