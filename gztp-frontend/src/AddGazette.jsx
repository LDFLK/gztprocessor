import React, { useState } from 'react';
import axios from 'axios';
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    TextField,
    FormControlLabel,
    RadioGroup,
    Radio,
    CircularProgress
} from '@mui/material';

const AddGazette = ({ onAdd }) => {
    const [open, setOpen] = useState(false);
    const [gazetteNumber, setGazetteNumber] = useState('');
    const [gazetteDate, setGazetteDate] = useState('');
    const [gazetteType, setGazetteType] = useState('');
    const [loading, setLoading] = useState(false);

    const handleOpen = () => setOpen(true);

    const handleClose = () => {
        setGazetteNumber('');
        setGazetteDate('');
        setGazetteType('');
        setOpen(false);
    };

    const handleSubmit = async () => {
        if (!gazetteNumber || !gazetteDate || !gazetteType) return;

        const endpoint = `http://localhost:8000/mindep/${gazetteType === 'initial' ? 'initial' : 'amendment'}/${gazetteDate}/${gazetteNumber}`;
        try {
            setLoading(true);
            const response = await axios.get(endpoint);

            if (response.data && response.data.error) {
                alert(response.data.error); // show the error from backend
                return;
            }
            if (gazetteType == 'initial') {
                onAdd({
                    gazetteNumber,
                    gazetteDate,
                    gazetteType,
                    transactions: response.data,

                });

            }
            else {
                onAdd({
                    gazetteNumber,
                    gazetteDate,
                    gazetteType,
                    adds: response.data.transactions.adds,
                    terminates: response.data.transactions.terminates,
                    moves: response.data.transactions.moves
                });

            }
            handleClose();
        } catch (error) {
            console.error('Error adding gazette:', error);
            alert('Failed to add gazette. Check the console for details.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Button
                variant="contained"
                onClick={handleOpen}
                sx={{
                    cursor: 'pointer',
                    borderRadius: '12px',
                    border: '2px solid #1976d2',
                    backgroundColor: '#1976d2',
                }}
            >
                <strong>add</strong>
            </Button>

            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add Gazette</DialogTitle>
                <DialogContent>
                    <TextField
                        margin="dense"
                        label="Gazette Number"
                        fullWidth
                        value={gazetteNumber}
                        onChange={(e) => setGazetteNumber(e.target.value)}
                    />
                    <TextField
                        margin="dense"
                        label="Gazette Date"
                        type="date"
                        fullWidth
                        InputLabelProps={{ shrink: true }}
                        value={gazetteDate}
                        onChange={(e) => setGazetteDate(e.target.value)}
                    />
                    <RadioGroup
                        row
                        name="gazette-type"
                        value={gazetteType}
                        onChange={(e) => setGazetteType(e.target.value)}
                        sx={{ mt: 2 }}
                    >
                        <FormControlLabel value="initial" control={<Radio />} label="Initial" />
                        <FormControlLabel value="amendment" control={<Radio />} label="Amendment" />
                    </RadioGroup>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose} color="secondary">Cancel</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        color="primary"
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Add'}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};

export default AddGazette;
