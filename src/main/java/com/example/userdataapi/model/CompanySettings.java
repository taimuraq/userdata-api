package com.example.userdataapi.model;

import lombok.Data;

@Data
public class CompanySettings {
  private String unitId;
  private String settingName;
  private String settingValue;
  private String displayValue;
}

