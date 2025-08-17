import React from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Button,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";

export default function InitialPreview({
  transactions,
  expandedMinisters,
  toggleMinister,
  handleMinisterNameChange,
  handleAddMinister,
  handleDeleteMinister,
  handleDeptNameChange,
  handleAddDepartment,
  handleDeleteDepartment,
  handleAddPreviousMinistry,
  handleRemovePreviousMinistry,
  handlePreviousMinistryChange,
  handleToggleMove,
  isMoved,
  moveList,
  handleRemoveMove,
  handleApproveCommit,
  committing,
}) {
  return (
    <Paper sx={{ p: 3, borderRadius: 3, boxShadow: 3 }}>
      <Box sx={{ display: "flex", flexDirection: "row", gap: 5 }}>
        <Box sx={{ flex: 1 }}>
          {transactions.map((min, idx) => (
            <Box
              key={idx}
              mb={4}
              sx={{
                bgcolor: "#e3f2fd",
                borderRadius: 2,
                p: 3,
                boxShadow: 2,
                borderLeft: "6px solid #1976d2",
              }}
            >
              {/* Minister header with toggle */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  mb: 2,
                  cursor: "pointer",
                  userSelect: "none",
                }}
                onClick={() => toggleMinister(idx)}
              >
                {expandedMinisters[idx] ? (
                  <KeyboardArrowDownIcon color="primary" />
                ) : (
                  <KeyboardArrowRightIcon color="primary" />
                )}
                <TextField
                  label={`Minister ${idx + 1}`}
                  variant="standard"
                  value={min.name}
                  onChange={(e) => handleMinisterNameChange(idx, e.target.value)}
                  disabled={committing}
                  fullWidth
                  sx={{
                    ml: 1,
                    fontWeight: "bold",
                    "& .MuiInputBase-input": { fontWeight: 600 },
                  }}
                />
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAddMinister(idx);
                  }}
                  disabled={committing}
                  sx={{ border: "1px dashed #1976d2", color: "#1976d2" }}
                  aria-label="Add Minister"
                >
                  <AddIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteMinister(idx);
                  }}
                  disabled={committing || transactions.length <= 1}
                  sx={{ border: "1px dashed #d32f2f", color: "#d32f2f" }}
                  aria-label="Remove Minister"
                >
                  <RemoveIcon fontSize="small" />
                </IconButton>
              </Box>

              {/* Departments, collapsible */}
              {expandedMinisters[idx] && (
                <>
                  {(min.departments && min.departments.length > 0) ? (
                    min.departments.map((dept, i) => (
                      <Box
                        key={i}
                        ml={3}
                        mb={2}
                        position="relative"
                        sx={{
                          bgcolor: "#f0f4c3",
                          borderRadius: 2,
                          p: 2,
                          boxShadow: 1,
                          borderLeft: "4px solid #afb42b",
                        }}
                      >
                        <Box display="flex" alignItems="center" gap={1}>
                          <TextField
                            label={`Department ${i + 1}`}
                            variant="standard"
                            value={dept.name}
                            onChange={(e) =>
                              handleDeptNameChange(idx, i, e.target.value)
                            }
                            disabled={committing}
                            fullWidth
                          />
                          <IconButton
                            size="small"
                            onClick={() => handleAddDepartment(idx, i)}
                            disabled={committing}
                            sx={{ border: "1px dashed #afb42b", color: "#afb42b" }}
                            aria-label="Add Department"
                          >
                            <AddIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteDepartment(idx, i)}
                            disabled={committing}
                            sx={{ border: "1px dashed #d32f2f", color: "#d32f2f" }}
                            aria-label="Remove Department"
                          >
                            <RemoveIcon fontSize="small" />
                          </IconButton>
                        </Box>

                        {dept.show_previous_ministry ? (
                          <Box
                            display="flex"
                            alignItems="center"
                            gap={2}
                            mt={1}
                            sx={{ flexWrap: "wrap" }}
                          >
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={isMoved(min.name, dept.name)}
                                  onChange={() =>
                                    handleToggleMove(
                                      min.name,
                                      dept.name,
                                      dept.previous_ministry
                                    )
                                  }
                                  disabled={
                                    committing ||
                                    !(dept.previous_ministry &&
                                      dept.previous_ministry.trim())
                                  }
                                />
                              }
                              label={
                                <Box
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 1,
                                    flexWrap: "wrap",
                                  }}
                                >
                                  <Typography
                                    variant="body2"
                                    sx={{ minWidth: 160, fontWeight: 500 }}
                                  >
                                    Mark as a move from previous
                                  </Typography>
                                  <TextField
                                    variant="standard"
                                    value={dept.previous_ministry}
                                    onChange={(e) =>
                                      handlePreviousMinistryChange(idx, i, e.target.value)
                                    }
                                    disabled={committing}
                                    size="small"
                                    sx={{ width: "180px" }}
                                  />
                                </Box>
                              }
                            />
                            <Button
                              onClick={() => handleRemovePreviousMinistry(idx, i)}
                              size="small"
                              color="error"
                              disabled={committing}
                            >
                              Remove
                            </Button>
                          </Box>
                        ) : (
                          <Button
                            onClick={() => handleAddPreviousMinistry(idx, i)}
                            size="small"
                            sx={{ mt: 1 }}
                            disabled={committing}
                          >
                            ➕ Add Previous Ministry
                          </Button>
                        )}
                      </Box>
                    ))
                  ) : (
                    <Box
                      ml={3}
                      mb={2}
                      sx={{
                        bgcolor: "#f0f4c3",
                        borderRadius: 2,
                        p: 2,
                        boxShadow: 1,
                        borderLeft: "4px solid #afb42b",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontStyle: "italic",
                        color: "rgba(0,0,0,0.6)",
                      }}
                    >
                      <Typography>No departments added yet.</Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleAddDepartment(idx, -1)}
                        disabled={committing}
                        sx={{ borderColor: "#afb42b", color: "#afb42b" }}
                        aria-label="Add Department"
                      >
                        ➕ Add Department
                      </Button>
                    </Box>
                  )}
                </>
              )}
            </Box>
          ))}

          <Button
            variant="contained"
            color="success"
            sx={{ mt: 3 }}
            onClick={handleApproveCommit}
            disabled={committing}
          >
            {committing ? "Committing..." : "Approve & Commit Gazette"}
          </Button>
        </Box>

        {moveList.length > 0 && (
          <Box
            sx={{
              flex: 1,
              bgcolor: "#fafafa",
              border: "1px solid #ddd",
              p: 3,
              borderRadius: 3,
              boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
              height: "fit-content",
              maxHeight: 300,
              overflowY: "auto",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
                Departments Marked as Moves
              </Typography>
            </Box>

            {moveList.map(({ dName, prevMinistry, mName }, i) => (
              <Box
                key={i}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "#e8f0fe",
                  borderRadius: 2,
                  p: 1.2,
                  mb: 1,
                  boxShadow: "inset 0 0 5px rgba(25, 118, 210, 0.2)",
                  transition: "background-color 0.2s",
                  "&:hover": {
                    backgroundColor: "#d0dffe",
                  },
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  “{dName}” moved from <strong>{prevMinistry}</strong> to <strong>{mName}</strong>
                </Typography>
                <IconButton
                  size="medium"
                  color="error"
                  onClick={() => handleRemoveMove(mName, dName)}
                  aria-label={`Remove move ${dName} from ${mName}`}
                  sx={{ ml: 1 }}
                  title="Remove this move"
                >
                  <RemoveIcon fontSize="medium" />
                </IconButton>
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Paper>
  );
}
