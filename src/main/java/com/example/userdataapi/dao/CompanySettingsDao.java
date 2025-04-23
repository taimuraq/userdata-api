package com.example.userdataapi.dao;

import com.example.userdataapi.model.CompanySettings;
import org.springframework.stereotype.Repository;

@Repository
public class CompanySettingsDao {

  public CompanySettings getByUnitId(String unitId) {
    // Mocking the data
    CompanySettings settings = new CompanySettings();
    settings.setUnitId(unitId);
    settings.setSettingName("timezone");
    settings.setSettingValue("UTC");
    return settings;
  }

  public void save(CompanySettings settings) {
    // Mock save logic
    System.out.println("Saved settings for unitId: " + settings.getUnitId());
  }
}
