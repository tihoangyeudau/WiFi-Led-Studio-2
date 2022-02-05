import { useState } from 'react';
import useStore from '../../utils/apiStore';
import { Link, TextField, Dialog, DialogActions, DialogContent, DialogTitle, Button, Typography } from '@material-ui/core';

const AddSceneDialog = () => {  
  const [name, setName] = useState('');
  const [image, setImage] = useState('');
  const [overwrite, setOverwrite] = useState(false)

  const addScene = useStore((state) => state.addScene);
  const getScenes = useStore((state) => state.getScenes);
  const scenes = useStore((state) => state.scenes);
  const open = useStore((state) => state.dialogs.addScene?.open || false);
  const setDialogOpenAddScene = useStore((state) => state.setDialogOpenAddScene);

  const handleClose = () => {
    setDialogOpenAddScene(false);
  };
  const handleAddScene = (e) => {

    addScene({ name, scene_image: image }).then(() => {
      getScenes();
    });
    setName('');
    setImage('');
    setDialogOpenAddScene(false);
  };

  return (
    <Dialog open={open} onClose={handleClose} aria-labelledby="form-dialog-title">
    <DialogTitle id="form-dialog-title">Thêm cảnh</DialogTitle>
    <DialogContent>
        Hình ảnh là tùy chọn và có thể là một trong số:
        <ul style={{ paddingLeft: '1rem' }}>
        <li>iconName <Link href="https://material-ui.com/components/material-icons/">Tìm biểu tượng MUI tại đây</Link>        
        <Typography color="textSecondary" variant="subtitle1"><em>ví dụ: bùng phát, báo động</em></Typography></li>
        <li>mdi:icon-name <Link href="https://materialdesignicons.com">Tìm các biểu tượng Material Design tại đây</Link>
        <Typography color="textSecondary" variant="subtitle1"><em>ví dụ: mdi:balloon, mdi:led-strip-variant</em></Typography></li>
        <li>image:custom-url
        <Typography color="textSecondary" variant="subtitle1" style={{ wordBreak: 'break-all'}}><em>ví dụ: image:https://i.ytimg.com/vi/4G2unzNoOnY/maxresdefault.jpg</em></Typography></li>
        </ul>
      
      <TextField
        autoFocus
        margin="dense"
        id="name"
        label="Tên"
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onBlur={(e) => {          
          setOverwrite(Object.keys(scenes).indexOf(e.target.value.toLowerCase()) > -1)
        }}
        error={overwrite}
        helperText={overwrite && "Cảnh đã có!"}
        required
        fullWidth
      />
      <TextField
        margin="dense"
        id="scene_image"
        label="Hình ảnh"
        type="text"
        value={image}
        onChange={(e) => setImage(e.target.value)}
        fullWidth
      />
    </DialogContent>
    <DialogActions>
      <Button onClick={handleClose}>
        Huỷ
      </Button>
      <Button onClick={handleAddScene}>
      {overwrite ? 'Ghi đè' : 'Thêm'}
      </Button>
    </DialogActions>
  </Dialog>
  )
}

export default AddSceneDialog
