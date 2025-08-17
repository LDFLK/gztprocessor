import { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Button, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, InputBase, Avatar, Divider, CircularProgress, IconButton, Collapse, } from '@mui/material';
import { styled, alpha } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import AddGazette from './AddGazette';
import TransactionPreview from './TransactionPreview';
import ErrorIcon from '@mui/icons-material/Error';

const Search = styled('div')(({ theme }) => ({
    position: 'relative',
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.grey[900], 0.05),
    '&:hover': {
        backgroundColor: alpha(theme.palette.grey[900], 0.1),
    },
    marginLeft: theme.spacing(2),

}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
    padding: theme.spacing(0, 2),
    height: '100%',
    position: 'absolute',
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
    color: 'inherit',
    width: '100%',
    '& .MuiInputBase-input': {
        padding: theme.spacing(1.2, 1, 1.2, 0),
        paddingLeft: `calc(1em + ${theme.spacing(4)})`,
        transition: theme.transitions.create('width'),
        width: '100%',
    },
}));

const Data = {
    presidents: [
        {
            name: 'President A',
            imageUrl: '',
            created: '2022-01-01',
            gazettes: [],
        },
        {
            name: 'President B',
            imageUrl: '',
            created: '2024-01-01',
            gazettes: [],
        },
        {
            name: 'President C',
            imageUrl: '',
            created: '2024-01-01',
            gazettes: [],
        },

    ],
};

function highlightMatch(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark style="background-color: #ffe58f;">$1</mark>');
}

export default function StateTable() {
    const [data, setData] = useState(Data);
    const [selectedPresidentIndex, setSelectedPresidentIndex] = useState(0);
    const [selectedGazetteIndex, setSelectedGazetteIndex] = useState(0);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [expanded, setExpanded] = useState(true);
    const [refreshFlag, setRefreshFlag] = useState(false);
    const [gazetteWarnings, setGazetteWarnings] = useState(() => {
        // Initially, no warnings
        return data.presidents[selectedPresidentIndex]?.gazettes?.map(() => false) || [];
    });

    const presidents = data.presidents || [];
    const selectedPresident = presidents[selectedPresidentIndex];
    const hasGazettes = selectedPresident?.gazettes?.length > 0;
    const selectedGazette = hasGazettes ? selectedPresident.gazettes[selectedGazetteIndex] : null;

    const filteredMinisters = selectedGazette?.ministers?.filter((minister) => {
        const query = searchQuery.toLowerCase();
        return (
            minister.name.toLowerCase().includes(query) ||
            minister.departments.some((d) => d.toLowerCase().includes(query))
        );
    }) || [];

    useEffect(() => {
        const loadState = async () => {
            const currentPresident = data.presidents[selectedPresidentIndex];
            const currentGazette = currentPresident?.gazettes?.[selectedGazetteIndex];
            if (!currentGazette) return;

            // Only load if ministers not yet set or explicitly null to avoid infinite loops
            if (currentGazette.ministers !== null && currentGazette.ministers !== undefined) return;

            setLoading(true);
            try {
                const res = await axios.get(
                    `http://localhost:8000/mindep/state/${currentGazette.date}/${currentGazette.number}`
                );
                const backendMinisters = res.data.state?.ministers;

                const updatedData = JSON.parse(JSON.stringify(data));

                if (backendMinisters?.length > 0) {
                    updatedData.presidents[selectedPresidentIndex].gazettes[selectedGazetteIndex].ministers = backendMinisters;
                } else {
                    // If no backend ministers for current gazette, fallback to previous gazette ministers
                    if (selectedGazetteIndex > 0) {
                        const prevMinisters = currentPresident.gazettes[selectedGazetteIndex - 1]?.ministers || [];
                        updatedData.presidents[selectedPresidentIndex].gazettes[selectedGazetteIndex].ministers = prevMinisters;
                    } else {
                        // No previous gazette, so empty ministers
                        updatedData.presidents[selectedPresidentIndex].gazettes[selectedGazetteIndex].ministers = [];
                    }
                }

                setData(updatedData);
            } catch (err) {
                console.warn("Failed to fetch state:", err);
            } finally {
                setLoading(false);
            }
        };

        loadState();
    }, [data, selectedPresidentIndex, selectedGazetteIndex, refreshFlag]);

    useEffect(() => {
        const fetchGazettes = async () => {
            try {
                // Fetch committed gazettes
                const resCommitted = await axios.get('http://localhost:8000/mindep/state/gazettes/2022-07-22/2022-09-22');
                const committedGazettes = resCommitted.data || [];
                console.log('Committed:', committedGazettes);

                // Fetch draft gazettes
                const resDraft = await axios.get('http://localhost:8000/info/mindep/2022-07-22/2022-09-22');
                const draftGazettes = resDraft.data || [];
                console.log('Drafts:', draftGazettes);

                // Map committed
                const enrichedCommitted = committedGazettes.map(g => ({
                    number: g.gazette_number,
                    date: g.date,
                    committed: true,
                    ministers: null,
                    transactions: null,
                    terminates: [],
                    moves: [],
                    adds: [],
                    warning: false,
                    gazette_format: null,
                }));

                // Map drafts and normalize warning to a real boolean
                const enrichedDrafts = draftGazettes.map(g => ({
                    number: g.gazette_number,
                    date: g.date,
                    committed: false,
                    ministers: null,
                    transactions: null,
                    terminates: [],
                    moves: [],
                    adds: [],
                    warning: Boolean(Number(g.warning)),
                    gazette_format: g.gazette_format
                }));

                // Attach draft warnings to committed if both exist
                enrichedCommitted.forEach(cGazette => {
                    const draftMatch = enrichedDrafts.find(dGazette => dGazette.number === cGazette.number);
                    if (draftMatch) {
                        cGazette.warning = draftMatch.warning;
                        cGazette.gazette_format = draftMatch.gazette_format
                    }
                });

                // Filter out drafts that have a committed counterpart
                const committedNumbers = new Set(enrichedCommitted.map(g => g.number));
                const filteredDrafts = enrichedDrafts.filter(g => !committedNumbers.has(g.number));

                const allGazettes = [...enrichedCommitted, ...filteredDrafts]
                    .sort((a, b) => new Date(a.date) - new Date(b.date));

                // Update main data state
                const updated = JSON.parse(JSON.stringify(Data));
                updated.presidents[selectedPresidentIndex].gazettes = allGazettes;
                setData(updated);
                console.log(updated)
                // Sync warning array with fetched data
                setGazetteWarnings(allGazettes.map(g => g.warning || false));

            } catch (err) {
                console.error("Failed to fetch gazettes:", err);
            }
        };

        fetchGazettes();
    }, []);



    const handleGazetteCommitted = (committedIndex) => {
        setGazetteWarnings((prev) => {
            const gazettes = data.presidents[selectedPresidentIndex]?.gazettes || [];
            const newWarnings = prev.slice();

            // Clear warning on committed gazette
            newWarnings[committedIndex] = false;

            // Persist updated warning to drafts table
            const committedGazette = gazettes[committedIndex];
            axios.post(
                `http://localhost:8000/transactions/${committedGazette.number}/warning`,
                { warning: false }
            ).catch(err => console.error("Failed to update warning:", err));

            // Mark all gazettes after committedIndex as needing redo
            for (let i = committedIndex + 1; i < gazettes.length; i++) {
                newWarnings[i] = true;

                // Persist warning to drafts table
                axios.post(
                    `http://localhost:8000/transactions/${gazettes[i].number}/warning`,
                    { warning: true }
                ).catch(err => console.error("Failed to update warning:", err));
            }

            return newWarnings;
        });
    };


    const getLatestUpdatedState = () => {
        const updatedData = JSON.parse(JSON.stringify(data));
        const currentPresident = data.presidents[selectedPresidentIndex];
        const prevMinisters = currentPresident.gazettes[selectedGazetteIndex - 1]?.ministers || [];
        updatedData.presidents[selectedPresidentIndex].gazettes[selectedGazetteIndex].ministers = prevMinisters;
        setData(updatedData);
    }

    return (
        <Box p={4} sx={{ maxWidth: '1000px', mx: 'auto' }}>
            <Typography variant="h4" gutterBottom fontWeight="bold">Org State</Typography>
            <Divider sx={{ my: 3 }} />

            {/* Presidents */}
            {presidents.length === 0 ? (
                <>
                    <Typography variant="body1" color="text.secondary">⚠️ No presidents available.</Typography>
                    <Button> Add President </Button>
                </>
            ) : (
                <Box display="flex" gap={14} mb={4}>
                    {presidents.map((pres, idx) => (
                        <Box
                            key={idx}
                            onClick={() => {
                                setSelectedPresidentIndex(idx);
                                setSelectedGazetteIndex(0);
                            }}
                            sx={{
                                textAlign: 'center',
                                cursor: 'pointer',
                                transform: idx === selectedPresidentIndex ? 'scale(1.5)' : 'scale(1)',
                                transition: 'transform 0.3s',
                            }}
                        >
                            <Avatar src={pres.imageUrl} sx={{ width: 36, height: 36, mb: 1, ml: 2.5, boxShadow: idx === selectedPresidentIndex ? 4 : 1 }} />
                            <Typography variant="body1" fontWeight="medium">{pres.name}</Typography>
                            <Typography variant="caption" color="text.secondary">{pres.created?.split('-')[0] || 'N/A'}</Typography>
                        </Box>
                    ))}
                </Box>
            )}

            {/* Gazette Tabs */}
            {hasGazettes ? (
                <>
                    <Box
                        sx={{
                            display: 'flex',
                            overflowX: 'auto',
                            whiteSpace: 'nowrap',
                            mb: 3,
                            gap: 2,
                            paddingBottom: 1,
                        }}
                    >
                        {selectedPresident.gazettes.map((gazette, gIdx) => (
                            <Box
                                key={gIdx}
                                sx={{ display: 'inline-block', mr: 2, position: 'relative' }}

                            >
                                <Paper
                                    elevation={gIdx === selectedGazetteIndex ? 6 : 1}
                                    onClick={() => setSelectedGazetteIndex(gIdx)}
                                    sx={{
                                        px: 2,
                                        py: 1,
                                        cursor: 'pointer',
                                        borderRadius: '12px',
                                        border: gIdx === selectedGazetteIndex ? '2px solid #1976d2' : '1px solid #ddd',
                                        backgroundColor: gIdx === selectedGazetteIndex ? '#e0e8f0ff' : 'white',
                                        display: 'inline-block',
                                        backgroundColor: gazette.committed ? '#cce8baff' : '#e7c6c6ff'
                                    }}
                                >
                                    <Typography variant="body2" fontWeight="medium">
                                        {gazette.number}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {gazette.date}
                                    </Typography>
                                </Paper>

                                {/* Warning icon for gazettes with warnings */}
                                {gazetteWarnings[gIdx] && (
                                    <Box
                                        sx={{
                                            position: 'absolute',
                                            top: 1,   // lifted higher
                                            right: -3, // pushed outwards
                                            backgroundColor: 'white', // white circle background
                                            borderRadius: '50%',
                                            width: 12,
                                            height: 12,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            pointerEvents: 'none',
                                        }}
                                        title="This gazette must be redone because of earlier changes"
                                    >
                                        <ErrorIcon sx={{ fontSize: 17, color: '#d32f2f' }} />
                                    </Box>

                                )}

                            </Box>
                        ))}

                        <AddGazette
                            onAdd={({ gazetteNumber, gazetteDate, gazetteType, transactions, adds, moves, terminates }) => {
                                const newGazette = {
                                    number: gazetteNumber,
                                    date: gazetteDate,
                                    gazette_format: gazetteType,
                                    ministers: null,
                                    // If initial, use transactions; if amendment, use the trio
                                    transactions: gazetteType === 'initial' ? transactions : undefined,
                                    adds: gazetteType === 'amendment' ? adds || [] : [],
                                    moves: gazetteType === 'amendment' ? moves || [] : [],
                                    terminates: gazetteType === 'amendment' ? terminates || [] : [],
                                };

                                const updatedData = JSON.parse(JSON.stringify(data));
                                updatedData.presidents[selectedPresidentIndex].gazettes.push(newGazette);
                                const newGazetteIndex = updatedData.presidents[selectedPresidentIndex].gazettes.length - 1;

                                setData(updatedData);

                                setGazetteWarnings((prevWarnings) => {
                                    const hasWarnings = prevWarnings.some((w) => w === true);
                                    return [...prevWarnings, hasWarnings]; // append true if any warning exists, else false
                                });

                                setSelectedGazetteIndex(newGazetteIndex); // auto-switch to new gazette
                            }}
                        />
                    </Box>

                    {/* Expand/Collapse Header */}
                    <Box
                        onClick={() => setExpanded((prev) => !prev)}
                        sx={{
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            userSelect: 'none',
                            mb: 1,
                            justifyContent: 'space-between',

                        }}
                    >
                        <Typography variant="h6"> Current State </Typography>
                        <IconButton
                            size="small"
                            aria-label={expanded ? 'Collapse section' : 'Expand section'}
                            sx={{
                                transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                                transition: '0.3s',
                            }}
                        >
                            {expanded ? <KeyboardArrowDownIcon /> : <KeyboardArrowUpIcon />}
                        </IconButton>
                    </Box>

                    {/* Collapsible Search + Table */}
                    <Collapse in={expanded} timeout="auto" unmountOnExit>
                        {/* Search */}
                        <Search sx={{ mb: 2 }}>
                            <SearchIconWrapper><SearchIcon /></SearchIconWrapper>
                            <StyledInputBase
                                placeholder="Search ministers or departments"
                                inputProps={{ 'aria-label': 'search' }}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </Search>

                        {/* Table */}
                        {loading ? (
                            <Box display="flex" justifyContent="center" mt={4}>
                                <CircularProgress />
                            </Box>
                        ) : !selectedGazette?.ministers ? (
                            <Paper
                                sx={{
                                    p: 4,
                                    mt: 4,
                                    borderRadius: 3,
                                    boxShadow: 3,
                                    textAlign: 'center',
                                    bgcolor: '#fff3cd', // light warning bg
                                    color: '#856404', // dark warning text
                                }}
                            >
                                <Typography variant="h6" gutterBottom>⚠️ No ministers available for this gazette.</Typography>
                                <Typography variant="body2">Please select another gazette or add ministers.</Typography>
                            </Paper>
                        ) : (
                            <TableContainer
                                component={Paper}
                                sx={{
                                    borderRadius: 4,
                                    mt: 2,
                                    boxShadow: 4,
                                    maxHeight: 300,
                                    overflowY: 'auto',
                                    bgcolor: 'background.paper',
                                    border: '1px solid #ddd',
                                }}
                            >
                                <Table stickyHeader aria-label="ministers table">
                                    <TableHead sx={{ backgroundColor: '#1976d2' }}>
                                        <TableRow>
                                            <TableCell
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: 'black',
                                                    fontSize: '1rem',
                                                    py: 1.5,
                                                    px: 2,
                                                    borderBottom: 'none',
                                                }}
                                            >
                                                Minister
                                            </TableCell>

                                            <TableCell
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: 'black',
                                                    fontSize: '1rem',
                                                    py: 1.5,
                                                    px: 2,
                                                    borderBottom: 'none',
                                                }}
                                            >
                                                <Box
                                                    sx={{
                                                        display: 'flex',
                                                        justifyContent: 'space-between',
                                                        alignItems: 'center',
                                                        width: '100%',
                                                    }}
                                                >
                                                    Departments
                                                    {gazetteWarnings[selectedGazetteIndex] && (
                                                        <Button
                                                            size="small"
                                                            variant="outlined"
                                                            onClick={() => getLatestUpdatedState()}
                                                        >
                                                            Get latest updated state
                                                        </Button>
                                                    )}
                                                </Box>
                                            </TableCell>
                                        </TableRow>
                                    </TableHead>

                                    <TableBody>
                                        {filteredMinisters.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={2} sx={{ textAlign: 'center', py: 3 }}>
                                                    <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                                        No matching records found.
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            filteredMinisters.map((minister, idx) => (
                                                <TableRow
                                                    hover
                                                    key={idx}
                                                    sx={{
                                                        bgcolor: idx % 2 === 0 ? 'action.hover' : 'background.default',
                                                    }}
                                                >
                                                    <TableCell
                                                        sx={{ py: 1.5, px: 2, minWidth: 150 }}
                                                        dangerouslySetInnerHTML={{
                                                            __html: `${idx + 1}. ${highlightMatch(minister.name, searchQuery)}`,
                                                        }}
                                                    />
                                                    <TableCell sx={{ py: 1.5, px: 2 }}>
                                                        <ol
                                                            style={{
                                                                margin: 0,
                                                                paddingLeft: '1.25rem',
                                                                fontSize: '0.9rem',
                                                                color: '#444',
                                                                listStyleType: 'decimal',
                                                            }}
                                                        >
                                                            {minister.departments.map((dept, dIdx) => (
                                                                <li
                                                                    key={dIdx}
                                                                    dangerouslySetInnerHTML={{ __html: highlightMatch(dept, searchQuery) }}
                                                                    style={{ marginBottom: '0.25rem' }}
                                                                />
                                                            ))}
                                                        </ol>
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        )}

                    </Collapse>
                    <TransactionPreview
                        transactions={
                            Array.isArray(selectedGazette?.transactions)
                                ? selectedGazette.transactions
                                : Array.isArray(selectedGazette)
                                    ? selectedGazette
                                    : []
                        }
                        moves={
                            Array.isArray(selectedGazette?.moves)
                                ? selectedGazette.moves
                                : Array.isArray(selectedGazette?.transactions?.moves)
                                    ? selectedGazette.transactions.moves
                                    : []
                        }

                        adds={
                            Array.isArray(selectedGazette?.adds)
                                ? selectedGazette.adds
                                : Array.isArray(selectedGazette?.transactions?.adds)
                                    ? selectedGazette.transactions.adds
                                    : []
                        }
                        terminates={
                            Array.isArray(selectedGazette?.terminates)
                                ? selectedGazette.terminates
                                : Array.isArray(selectedGazette?.transactions?.terminates)
                                    ? selectedGazette.transactions.terminates
                                    : []
                        }
                        selectedGazetteFormat={selectedGazette.gazette_format}
                        data={data}
                        selectedPresidentIndex={selectedPresidentIndex}
                        selectedGazetteIndex={selectedGazetteIndex}
                        setData={setData}
                        setRefreshFlag={setRefreshFlag}
                        onGazetteCommitted={handleGazetteCommitted}
                    />

                </>
            ) : (
                <Box
                    sx={{
                        display: 'flex',
                        overflowX: 'auto',
                        whiteSpace: 'nowrap',
                        mb: 3,
                        gap: 2,
                        paddingBottom: 1,
                    }}
                >
                    <Typography
                        sx={{
                            px: 2,
                            py: 1,
                            cursor: 'pointer',
                            borderRadius: '12px',
                            height: '40px',
                            display: 'inline-block',

                        }}
                        variant="body1" color="text.secondary">
                        No gazettes available for <strong>{selectedPresident.name}</strong>.
                    </Typography>
                    <AddGazette
                        onAdd={({ gazetteNumber, gazetteDate, gazetteType, transactions, adds, moves, terminates }) => {
                            const newGazette = {
                                number: gazetteNumber,
                                date: gazetteDate,
                                gazette_format: gazetteType,
                                ministers: null,
                                // If initial, use transactions; if amendment, use the trio
                                transactions: gazetteType === 'initial' ? transactions : undefined,
                                adds: gazetteType === 'amendment' ? adds || [] : [],
                                moves: gazetteType === 'amendment' ? moves || [] : [],
                                terminates: gazetteType === 'amendment' ? terminates || [] : [],
                            };

                            const updatedData = JSON.parse(JSON.stringify(data));
                            updatedData.presidents[selectedPresidentIndex].gazettes.push(newGazette);
                            const newGazetteIndex = updatedData.presidents[selectedPresidentIndex].gazettes.length - 1;

                            setData(updatedData);

                            setGazetteWarnings((prevWarnings) => {
                                const hasWarnings = prevWarnings.some((w) => w === true);
                                return [...prevWarnings, hasWarnings]; // append true if any warning exists, else false
                            });

                            setSelectedGazetteIndex(newGazetteIndex); // auto-switch to new gazette
                        }}
                    />
                </Box>
            )}
        </Box>

    );
}
