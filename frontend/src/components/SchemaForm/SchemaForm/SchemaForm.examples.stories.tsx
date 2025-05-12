import { Card, CardContent } from '@material-ui/core';
import { ComponentStory, ComponentMeta } from '@storybook/react';
// eslint-disable-next-line
import BladeSchemaForm from "./SchemaForm";

export default {
  /* 👇 The title prop is optional.
   * See https://storybook.js.org/docs/react/configure/overview#configure-story-loading
   * to learn how to generate automatic titles
   */
  title: 'UI Components/SchemaForm/Examples',
  component: BladeSchemaForm,
  argTypes: {
    type: {
      control: false,
    },
  },
  parameters: {
    options: {
      showPanel: true,
      panelPosition: 'bottom',
    },
  },
  decorators: [
    (Story) => (
      <Card style={{ maxWidth: 800 }}>
        <CardContent>{Story()}</CardContent>
      </Card>
    ),
  ],
} as ComponentMeta<typeof BladeSchemaForm>;

// eslint-disable-next-line
const Template: ComponentStory<typeof BladeSchemaForm> = (args) => <BladeSchemaForm {...args} />;

export const AddDeviceSkydimondUSB = Template.bind({});
AddDeviceSkydimondUSB.args = {
  schema: {
    properties: {
      name: {
        type: 'string',
        title: 'Name',
        description: 'Tên đèn',
      },
      icon_name: {
        type: 'string',
        title: 'Tên icon',
        description: 'https://material-ui.com/components/material-icons/',
        default: 'mdi:led-strip',
      },
      center_offset: {
        type: 'integer',
        title: 'Bù giữa',
        description: 'Số lượng LED bù vào trung tâm của đèn',
        default: 0,
      },
      refresh_rate: {
        type: 'int',
        enum: [10, 12, 16, 21, 32, 64],
        title: 'Tần số phát mầu',
        description: 'Tần số phát mầu mục tiêu được gửi đến đèn',
        default: 64,
      },
      com_port: {
        type: 'string',
        enum: ['COM1'],
        title: 'Cổng COM',
        description: 'Cổng COM cho đèn SkydimondUSB',
      },
      baudrate: {
        type: 'integer',
        minimum: 115200,
        title: 'Tốc độ truyền',
        description: 'Tốc độ truyền',
        default: 500000,
      },
      pixel_count: {
        type: 'integer',
        minimum: 1,
        title: 'Số Led',
        description: 'Số lượng led của đèn',
        default: 1,
      },
      color_order: {
        type: 'string',
        enum: ['RGB', 'RBG', 'GRB', 'BRG', 'GBR', 'BGR'],
        title: 'Thứ tự mầu',
        description: 'Thứ tự mầu',
        default: 'RGB',
      },
    },
    permitted_keys: [
      'name',
      'icon_name',
      'center_offset',
      'refresh_rate',
      'com_port',
      'baudrate',
      'pixel_count',
      'color_order',
    ],
    required: ['name', 'com_port', 'baudrate', 'pixel_count', 'color_order'],
  },
  model: {},
  // eslint-disable-next-line
  onModelChange: (e) => console.log(e),
  hideToggle: false,
};

export const AddDeviceRML = Template.bind({});
AddDeviceRML.args = {
  schema: {
    properties: {
      name: {
        type: 'string',
        title: 'Tên',
        description: 'Tên đèn',
      },
      icon_name: {
        type: 'string',
        title: 'Tên icon',
        description: 'https://material-ui.com/components/material-icons/',
        default: 'mdi:led-strip',
      },
      center_offset: {
        type: 'integer',
        title: 'Bù giữa',
        description: 'Số lượng LED bù vào trung tâm của đèn',
        default: 0,
      },
      refresh_rate: {
        type: 'int',
        enum: [10, 12, 16, 21, 32, 64],
        title: 'Tần số phát màu',
        description: 'Tần số phát màu mục tiêu mà điểm ảnh được gửi đến đèn',
        default: 64,
      },
      ip_address: {
        type: 'string',
        title: 'Địa chỉ IP',
        description: 'Tên máy chủ hoặc địa chỉ IP của đèn',
      },
      sync_mode: {
        type: 'string',
        enum: ['UDP', 'DDP'],
        title: 'Chế độ đồng bộ',
        description:
          'Giao thức truyền trực tuyến tới đèn. Khuyến nghị: UDP <480 LED, DDP> 480 LED',
        default: 'UDP',
      },
      timeout: {
        type: 'integer',
        minimum: 0,
        maximum: 255,
        title: 'Hết giờ',
        description: 'Thời gian giữa hiệu ứng của WiFi Led Studio tắt và hiệu ứng của đèn kích hoạt',
        default: 1,
      },
    },
    permitted_keys: [
      'name',
      'icon_name',
      'center_offset',
      'refresh_rate',
      'ip_address',
      'sync_mode',
      'timeout',
    ],
    required: ['name', 'ip_address'],
  },
  model: {},
  // eslint-disable-next-line
  onModelChange: (e) => console.log(e),
  hideToggle: false,
};

export const AddDeviceUDP = Template.bind({});
AddDeviceUDP.args = {
  schema: {
    properties: {
      name: {
        type: 'string',
        title: 'Tên',
        description: 'Tên đèn',
      },
      icon_name: {
        type: 'string',
        title: 'Tên icon',
        description: 'https://material-ui.com/components/material-icons/',
        default: 'mdi:led-strip',
      },
      center_offset: {
        type: 'integer',
        title: 'Bù giữa',
        description: 'Số lượng LED bù vào trung tâm của đèn',
        default: 0,
      },
      refresh_rate: {
        type: 'int',
        enum: [10, 12, 16, 21, 32, 64],
        title: 'Tần số phát mầu',
        description: 'Tần số phát mầu mục tiêu được gửi đến đèn',
        default: 64,
      },
      ip_address: {
        type: 'string',
        title: 'Địa chỉ IP',
        description: 'Tên máy chủ hoặc địa chỉ IP của đèn',
      },
      pixel_count: {
        type: 'integer',
        minimum: 1,
        title: 'Số Led',
        description: 'Number of individual pixels',
        default: 1,
      },
      port: {
        type: 'integer',
        minimum: 1,
        maximum: 65535,
        title: 'Cổng',
        description: 'Cổng giao tiếp UDP',
        default: 7778,
      },
      udp_packet_type: {
        type: 'string',
        enum: ['DRGB', 'WARLS', 'DRGBW', 'DNRGB', 'adaptive_smallest'],
        title: 'Loại gói UDP',
        description: 'Mã hóa gói RGB',
        default: 'DRGB',
      },
      timeout: {
        type: 'integer',
        minimum: 1,
        maximum: 255,
        title: 'Hết giờ',
        description:
          'Vài giây để đợi sau khi gói nhận được cuối cùng để nhường quyền kiểm soát thiết bị',
        default: 1,
      },
      minimise_traffic: {
        type: 'boolean',
        title: 'Giảm thiểu lưu lượng truy cập',
        description:
          'Sẽ không gửi các bản cập nhật nếu không có gì thay đổi trên đèn',
        default: true,
      },
    },
    permitted_keys: [
      'name',
      'icon_name',
      'center_offset',
      'refresh_rate',
      'ip_address',
      'pixel_count',
      'port',
      'udp_packet_type',
      'timeout',
      'minimise_traffic',
    ],
    required: ['name', 'ip_address', 'pixel_count', 'port', 'udp_packet_type'],
  },
  model: {},
  // eslint-disable-next-line
  onModelChange: (e) => console.log(e),
  hideToggle: false,
};

export const AddVirtual = Template.bind({});
AddVirtual.args = {
  schema: {
    properties: {
      name: {
        type: 'string',
        title: 'Tên',
        description: 'Tên đèn',
      },
      mapping: {
        type: 'string',
        enum: ['span', 'copy'],
        title: 'Mapping',
        description:
          'Span: Effect spans all segments. Copy: Effect copied on each segment',
        default: 'span',
      },
      icon_name: {
        type: 'string',
        title: 'Tên icon',
        description: 'Icon for the device*',
        default: 'mdi:led-strip-variant',
      },
      max_brightness: {
        type: 'number',
        minimum: 0,
        maximum: 1,
        title: 'Max Brightness',
        description: 'Max brightness for the device',
        default: 1,
      },
      center_offset: {
        type: 'integer',
        title: 'Bù giữa',
        description: 'Số lượng LED bù vào trung tâm của đèn',
        default: 0,
      },
      preview_only: {
        type: 'boolean',
        title: 'Preview Only',
        description: 'Preview the pixels without updating the devices',
        default: false,
      },
      transition_time: {
        type: 'number',
        minimum: 0,
        maximum: 5,
        title: 'Transition Time',
        description: 'Length of transition between effects',
        default: 0.4,
      },
      transition_mode: {
        type: 'string',
        enum: [
          'Add',
          'Tan biến',
          'Đẩy',
          'Trượt',
          'Mống mắt',
          'Xuyên trắng',
          'Xuyên đen',
          'None',
        ],
        title: 'Chế độ chuyển tiếp',
        description: 'Kiểu chuyển tiếp giữa các hiệu ứng',
        default: 'Add',
      },
      frequency_min: {
        type: 'integer',
        minimum: 20,
        maximum: 24000,
        title: 'Frequency Min',
        description: 'Hiệu ứng phản ứng âm thanh tần số thấp nhất của đèn ảo này',
        default: 20,
      },
      frequency_max: {
        type: 'integer',
        minimum: 20,
        maximum: 24000,
        title: 'Tần số tối đa',
        description: 'Hiệu ứng phản ứng âm thanh tần số cao nhất của đèn ảo này',
        default: 18000,
      },
    },
    permitted_keys: [
      'name',
      'mapping',
      'icon_name',
      'max_brightness',
      'center_offset',
      'preview_only',
      'transition_time',
      'transition_mode',
      'frequency_min',
      'frequency_max',
    ],
    required: ['name', 'mapping'],
  },
  model: {},
  // eslint-disable-next-line
  onModelChange: (e) => console.log(e),
  hideToggle: false,
};

export const AudioCard = Template.bind({});
AudioCard.args = {
  schema: {
    properties: {
      sample_rate: {
        type: 'integer',
        title: 'Tỉ lệ mẫu',
        default: 60,
      },
      mic_rate: {
        type: 'integer',
        title: 'Tỉ lệ thu âm',
        default: 48000,
      },
      fft_size: {
        type: 'integer',
        title: 'Kích thước Fft',
        default: 1024,
      },
      min_volume: {
        type: 'number',
        minimum: 0.2,
        maximum: 0.8,
        title: 'Âm lượng tối thiểu',
        default: 0.2,
      },
      audio_device: {
        type: 'string',
        enum: {
          0: 'MME: Microsoft Soundmapper - Input',
          1: 'MME: USB Headphones (USB PnP Audio D',
          2: 'MME: VoiceMeeter Output (VB-Audio Vo',
          3: 'MME: Mikrofon (Virtual Desktop Audio',
          10: 'Windows DirectSound: Primärer Soundaufnahmetreiber',
          11: 'Windows DirectSound: USB Headphones (USB PnP Audio Device)',
          12: 'Windows DirectSound: VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)',
          13: 'Windows DirectSound: Mikrofon (Virtual Desktop Audio)',
          26: 'Windows WASAPI: USB Headphones (USB PnP Audio Device)',
          27: 'Windows WASAPI: VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)',
          28: 'Windows WASAPI: Mikrofon (Virtual Desktop Audio)',
          30: 'Windows WDM-KS: Mikrofon (VDVAD Wave)',
          32: 'Windows WDM-KS: Eingang (Realtek HD Audio Line input)',
          33: 'Windows WDM-KS: Mikrofon (Realtek HD Audio Mic input)',
          35: 'Windows WDM-KS: Stereomix (Realtek HD Audio Stereo input)',
          37: 'Windows WDM-KS: Mikrofon (USB PnP Audio Device)',
          40: 'Windows WDM-KS: VoiceMeeter Output (VoiceMeeter vaio)',
          43: 'Windows WDM-KS: Kopfhörer (@System32\\drivers\\bthhfenum.sys,#2;%1 Hands-Free%0\r\n;(Jabra Elite 75t))',
        },
        title: 'Tên thiết bị âm thanh',
        default: 1,
      },
    },
    permitted_keys: ['min_volume', 'audio_device'],
    required: [],
  },
  model: {},
  // eslint-disable-next-line
  onModelChange: (e) => console.log(e),
  hideToggle: false,
};
