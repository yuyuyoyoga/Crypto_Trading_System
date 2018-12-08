
    
CREATE TABLE currency (
    currency_id     int not null auto_increment,
    currency_name   VARCHAR(255),
    last_price      float,
    primary key (currency_id)
);


CREATE TABLE general_ledger (
    ledger_id     int not null auto_increment,
    user_id       int NOT NULL,
    currency_id   int NOT NULL,
    type_id       int NOT NULL,
    trade_price   float,
    quantity      float,
    amount        float,
    gl            float,
    trade_date    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    primary key (ledger_id)
);


CREATE TABLE historical_rate (
    rate_id           int not null auto_increment,
    r_timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    historical_rate   float,
    currency_id       int,
    primary key (rate_id)
);


CREATE TABLE portfolio (
    portfolio_id    int not null auto_increment,
    user_id         int,
    currency_id     int,
    quantity        float,
    unrealized_gl   float,
    avg_cost        float,
    primary key (portfolio_id)
);


CREATE TABLE transaction_type (
    type_id            int not null auto_increment,
    transaction_type   VARCHAR(255),
    primary key (type_id)
    
);


CREATE TABLE user_info (
    user_id    int not null auto_increment,
    username   VARCHAR(255),
    password   VARCHAR(255),
    email      VARCHAR(255),
    balance    float,
    primary key (user_id)
);


ALTER TABLE general_ledger
    ADD CONSTRAINT general_ledger_currency_fk FOREIGN KEY ( currency_id )
        REFERENCES currency ( currency_id );

ALTER TABLE general_ledger
    ADD CONSTRAINT general_ledger_type_fk FOREIGN KEY ( type_id )
        REFERENCES transaction_type ( type_id );

ALTER TABLE general_ledger
    ADD CONSTRAINT general_ledger_user_info_fk FOREIGN KEY ( user_id )
        REFERENCES user_info ( user_id );

ALTER TABLE historical_rate
    ADD CONSTRAINT historical_rate_currency_fk FOREIGN KEY ( currency_id )
        REFERENCES currency ( currency_id );

ALTER TABLE portfolio
    ADD CONSTRAINT portfolio_user_info_fk FOREIGN KEY ( user_id )
        REFERENCES user_info ( user_id );
