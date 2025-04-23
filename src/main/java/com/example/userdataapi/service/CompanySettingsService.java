package com.example.userdataapi.service;

import com.example.userdataapi.dao.CompanySettingsDao;
import com.example.userdataapi.model.CompanySettings;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CompanySettingsService {

  private final CompanySettingsDao dao;

  public CompanySettings getSettingsByUnitId(String unitId) {
    return dao.getByUnitId(unitId);
  }

  public void saveSettings(CompanySettings settings) {
    dao.save(settings);
  }
}
