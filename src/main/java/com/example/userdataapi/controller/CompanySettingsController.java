package com.example.userdataapi.controller;

import com.example.userdataapi.model.CompanySettings;
import com.example.userdataapi.service.CompanySettingsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/companysettings")
@RequiredArgsConstructor
@Tag(name = "Company Settings")
public class CompanySettingsController {

  private final CompanySettingsService service;

  @Operation(summary = "Get settings by unit ID")
  @GetMapping("/unit-id/{unitId}")
  public ResponseEntity<CompanySettings> getByUnitId(@PathVariable String unitId) {
    return ResponseEntity.ok(service.getSettingsByUnitId(unitId));
  }

  @Operation(summary = "Save company settings")
  @PostMapping
  public ResponseEntity<Void> saveSettings(@RequestBody CompanySettings settings) {
    service.saveSettings(settings);
    return ResponseEntity.ok().build();
  }
}
