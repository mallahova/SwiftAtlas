db = db.getSiblingDB("swift_codes_db");
db.swift_codes.createIndex({ swiftCode: 1 }, { unique: true });
db.swift_codes.createIndex({ swiftCodePrefix8: 1, isHeadquarter: 1 });
db.swift_codes.createIndex({ countryISO2: 1 });