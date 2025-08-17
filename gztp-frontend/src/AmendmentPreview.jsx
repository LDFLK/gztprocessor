import React from "react";
import { Paper, Box, Typography, TextField, IconButton, Button } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";

const AmendmentPreview = ({
  adds,
  moves,
  terminates,
  handleChange,
  handleAddSection,
  handleDeleteSection,
  handleApproveCommitAmendment,
  committing
}) => {
  return (
    <Paper sx={{ p: 3, borderRadius: 3, boxShadow: 3, mt: 3 }}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>

        {/* Adds Section */}
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Typography variant="h6" gutterBottom>Adds</Typography>
            <IconButton
              size="small"
              onClick={() => handleAddSection("adds")}
              sx={{ border: "1px dashed #1976d2", color: "#1976d2" }}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Box>

          {adds.map((item, idx) => (
            <Box
              key={`add-${idx}`}
              sx={{
                bgcolor: "#e3f2fd",
                borderRadius: 2,
                p: 2,
                mb: 1,
                boxShadow: 1,
                borderLeft: "6px solid #1976d2",
                display: "flex",
                flexDirection: "row",
                gap: 1,
                alignItems: "center",
              }}
            >
              <TextField
                label="Department"
                variant="standard"
                value={item.department}
                onChange={(e) => handleChange("adds", idx, "department", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="To Ministry"
                variant="standard"
                value={item.to_ministry}
                onChange={(e) => handleChange("adds", idx, "to_ministry", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Position"
                variant="standard"
                type="number"
                value={item.position}
                onChange={(e) => handleChange("adds", idx, "position", e.target.value)}
                sx={{ width: 80 }}
              />
              <IconButton
                size="small"
                onClick={() => handleDeleteSection("adds", idx)}
                color='#1976d2'
              >
                <RemoveIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Box>

        {/* Terminates Section */}
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Typography variant="h6" gutterBottom>Terminates</Typography>
            <IconButton
              size="small"
              onClick={() => handleAddSection("terminates")}
              sx={{ border: "1px dashed #d32f2f", color: "#d32f2f" }}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Box>

          {terminates.map((item, idx) => (
            <Box
              key={`terminate-${idx}`}
              sx={{
                bgcolor: "#ffebee",
                borderRadius: 2,
                p: 2,
                mb: 1,
                boxShadow: 1,
                borderLeft: "6px solid #d32f2f",
                display: "flex",
                flexDirection: "row",
                gap: 1,
                alignItems: "center",
              }}
            >
              <TextField
                label="Department"
                variant="standard"
                value={item.department}
                onChange={(e) => handleChange("terminates", idx, "department", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="From Ministry"
                variant="standard"
                value={item.from_ministry}
                onChange={(e) => handleChange("terminates", idx, "from_ministry", e.target.value)}
                sx={{ flex: 1 }}
              />
              <IconButton
                size="small"
                onClick={() => handleDeleteSection("terminates", idx)}
                color='#d32f2f'
              >
                <RemoveIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Box>

        {/* Moves Section */}
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Typography variant="h6" gutterBottom>Moves</Typography>
            <IconButton
              size="small"
              onClick={() => handleAddSection("moves")}
              sx={{ border: "1px dashed #fb8c00", color: "#fb8c00" }}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Box>

          {moves.map((item, idx) => (
            <Box
              key={`move-${idx}`}
              sx={{
                bgcolor: "#fff3e0",
                borderRadius: 2,
                p: 2,
                mb: 1,
                boxShadow: 1,
                borderLeft: "6px solid #fb8c00",
                display: "flex",
                flexDirection: "row",
                gap: 1,
                alignItems: "center",
              }}
            >
              <TextField
                label="Department"
                variant="standard"
                value={item.department}
                onChange={(e) => handleChange("moves", idx, "department", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="From Ministry"
                variant="standard"
                value={item.from_ministry}
                onChange={(e) => handleChange("moves", idx, "from_ministry", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="To Ministry"
                variant="standard"
                value={item.to_ministry}
                onChange={(e) => handleChange("moves", idx, "to_ministry", e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Position"
                variant="standard"
                type="number"
                value={item.position}
                onChange={(e) => handleChange("moves", idx, "position", e.target.value)}
                sx={{ width: 80 }}
              />
              <IconButton
                size="small"
                onClick={() => handleDeleteSection("moves", idx)}
                color='#fb8c00'
              >
                <RemoveIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Box>

      </Box>

      <Button
        variant="contained"
        color="success"
        sx={{ mt: 3 }}
        onClick={handleApproveCommitAmendment}
        disabled={committing}
      >
        {committing ? "Committing..." : "Approve & Commit Gazette"}
      </Button>
    </Paper>
  );
};

export default AmendmentPreview;
