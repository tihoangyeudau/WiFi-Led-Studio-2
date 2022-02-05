import { Card, CardContent } from '@material-ui/core';
import { ComponentStory, ComponentMeta } from '@storybook/react';
// eslint-disable-next-line
import EffectSchemaForm from "./EffectSchemaForm";

export default {
  /* 👇 The title prop is optional.
   * See https://storybook.js.org/docs/react/configure/overview#configure-story-loading
   * to learn how to generate automatic titles
   */
  title: 'UI Components/SchemaForm/Examples',
  component: EffectSchemaForm,
  argTypes: {
    type: {
      control: false,
    },
  },
  decorators: [
    (Story) => (
      <Card style={{ maxWidth: 800 }}>
        <CardContent>{Story()}</CardContent>
      </Card>
    ),
  ],
  parameters: {
    options: {
      showPanel: true,
      panelPosition: 'bottom',
    },
  },
} as ComponentMeta<typeof EffectSchemaForm>;

// eslint-disable-next-line
const Template: ComponentStory<typeof EffectSchemaForm> = (args) => <EffectSchemaForm {...args} />;

export const EffectForm = Template.bind({});
EffectForm.storyName = 'Effect Schema';
EffectForm.args = {
  schema: {
    properties: {
      flip: {
        type: 'boolean',
        title: 'Lật',
        description: 'Lật hiệu ứng',
        default: false,
      },
      brightness: {
        type: 'number',
        minimum: 0,
        maximum: 1,
        title: 'Độ sáng',
        description: 'Độ sáng của đèn',
        default: 1,
      },
      background_brightness: {
        type: 'number',
        minimum: 0,
        maximum: 1,
        title: 'Độ sáng nền',
        description: 'Độ sáng của màu nền',
        default: 1,
      },
      gradient: {
        type: 'color',
        gradient: true,
        title: 'Dải mầu',
        description: 'Dải mầu để hiển thị trên hiệu ứng',
        default:
          'linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 120, 0) 14%, rgb(255, 200, 0) 28%, rgb(0, 255, 0) 42%, rgb(0, 199, 140) 56%, rgb(0, 0, 255) 70%, rgb(128, 0, 128) 84%, rgb(255, 0, 178) 98%)',
      },
      gradient_roll: {
        type: 'number',
        minimum: 0,
        maximum: 10,
        title: 'Cuộn dải mầu',
        description: 'Số lượng thay đổi dải mầu',
        default: 0,
      },
      mirror: {
        type: 'boolean',
        title: 'Phản chiếu',
        description: 'Phản chiếu hiệu ứng',
        default: false,
      },
      blur: {
        type: 'number',
        minimum: 0,
        maximum: 10,
        title: 'Mờ',
        description: 'Làm mờ hiệu ứng',
        default: 2,
      },
      decay: {
        type: 'number',
        minimum: 0,
        maximum: 1,
        title: 'Phân rã',
        description: 'Tỷ lệ phân rã màu sắc',
        default: 0.7,
      },
      multiplier: {
        type: 'number',
        minimum: 0,
        maximum: 1,
        title: 'Hệ số nhân',
        description: 'Làm cho thanh nháy lớn hơn / nhỏ hơn',
        default: 0.5,
      },
      background_color: {
        type: 'color',
        gradient: false,
        title: 'Màu nền',
        description: 'Mầu của nền hiệu ứng',
        default: '#000000',
      },
      frequency_range: {
        type: 'string',
        enum: ['Beat', 'Bass', 'Lows (beat+bass)', 'Mids', 'High'],
        title: 'Dải tần số',
        description: 'Dải tần số để phát hiện nhịp',
        default: 'Lows (beat+bass)',
      },
      invert_roll: {
        type: 'boolean',
        title: 'Đảo ngược cuộn',
        description: 'Đảo ngược hướng của cuộn dải mầu',
        default: false,
      },
    },
  },
  model: {
    blur: 2,
    decay: 0.7,
    frequency_range: 'Lows (beat+bass)',
    brightness: 1,
    mirror: false,
    invert_roll: false,
    multiplier: 0.5,
    gradient: 'linear-gradient(90deg, #00ffff 0.00%,#0000ff 100.00%)',
    gradient_roll: 0,
    background_color: '#000080',
    background_brightness: 1,
    flip: false,
  },
  handleEffectConfig: (e) => {
    // eslint-disable-next-line no-console
    console.log('Cập nhật hiệu ứng', e);
    return true;
  },
};
