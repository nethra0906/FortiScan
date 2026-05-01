app.post('/execute', (req, res) => {
  const { action } = req.body;

  const allowedActions = {
    'backup': () => runSafeCommand('backup-script.sh'),
    'status': () => runSafeCommand('system-status.sh'),
    'restart-service': (service) => runSafeCommand(`restart-service.sh ${escapeShellArg(service)}`, true) // only if service name is strictly validated
  };

  if (!allowedActions[action]) {
    return res.status(400).json({ error: 'Invalid action' });
  }

  // execute only pre-approved logic
});