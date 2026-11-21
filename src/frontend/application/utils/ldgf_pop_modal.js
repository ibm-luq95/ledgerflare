/**
 * ldgf_pop_modal.js
 * A native, vanilla ES6 Modal controller bypassing Preline.
 */

export class LdgfModal {
    constructor(elementSelector, options = {}) {
        this.modal = typeof elementSelector === 'string' ? document.querySelector(elementSelector) : elementSelector;
        if (!this.modal) return;
        
        this.dialog = this.modal.querySelector('.ldgf-modal-dialog');
        this.options = { backdrop: 'static', keyboard: true, ...options };
        
        this.isOpen = false;
        this.triggerElement = null;
        this.focusables = [];
        
        this._handleKeydown = this._handleKeydown.bind(this);
        this._handleBackdropClick = this._handleBackdropClick.bind(this);
        
        this._init();
    }

    _init() {
        // Bind dismiss buttons inside this specific modal
        const dismissButtons = this.modal.querySelectorAll('[data-ldgf-dismiss="modal"]');
        dismissButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
            });
        });

        // Bind backdrop click
        this.modal.addEventListener('click', this._handleBackdropClick);
    }

    open(trigger = null) {
        if (this.isOpen) return;

        // Custom Event: before open
        const showEvent = new CustomEvent('show.ldgf.modal', { cancelable: true });
        this.modal.dispatchEvent(showEvent);
        if (showEvent.defaultPrevented) return;

        this.triggerElement = trigger;
        this._lockScroll();

        // Reveal in DOM
        this.modal.classList.remove('hidden');
        
        // Force reflow for CSS transitions
        void this.modal.offsetWidth;

        // Trigger animations (Opacity & Scale)
        this.modal.classList.replace('opacity-0', 'opacity-100');
        this.dialog.classList.replace('scale-95', 'scale-100');

        this._setupAccessibility();
        this.isOpen = true;

        // Custom Event: opened
        this.modal.dispatchEvent(new CustomEvent('shown.ldgf.modal'));
    }

    close() {
        if (!this.isOpen) return;

        // Custom Event: before close
        const hideEvent = new CustomEvent('hide.ldgf.modal', { cancelable: true });
        this.modal.dispatchEvent(hideEvent);
        if (hideEvent.defaultPrevented) return;

        // Trigger animations (Opacity & Scale)
        this.modal.classList.replace('opacity-100', 'opacity-0');
        this.dialog.classList.replace('scale-100', 'scale-95');

        // Wait for CSS transition (200ms based on Tailwind classes) before hiding from DOM
        const onTransitionEnd = (e) => {
            if (e.target !== this.modal && e.target !== this.dialog) return;
            this.dialog.removeEventListener('transitionend', onTransitionEnd);
            
            this.modal.classList.add('hidden');
            this._unlockScroll();
            this._removeAccessibility();

            if (this.triggerElement) {
                this.triggerElement.focus();
            }
            
            this.isOpen = false;
            // Custom Event: closed
            this.modal.dispatchEvent(new CustomEvent('hidden.ldgf.modal'));
        };

        this.dialog.addEventListener('transitionend', onTransitionEnd);
    }

    // --- Internal Handlers ---

    _handleBackdropClick(e) {
        // Did they click the gray background exactly?
        if (e.target === this.modal) {
            if (this.options.backdrop === 'static') {
                // Static Backdrop Bump Animation
                this.dialog.classList.add('scale-105');
                setTimeout(() => this.dialog.classList.remove('scale-105'), 150);
                this.modal.dispatchEvent(new CustomEvent('hidePrevented.ldgf.modal'));
            } else {
                this.close();
            }
        }
    }

    _handleKeydown(e) {
        if (e.key === 'Escape' && this.options.keyboard) {
            e.preventDefault();
            this.close();
        }
        
        if (e.key === 'Tab') {
            this._trapFocus(e);
        }
    }

    // --- Scroll & A11y Utils ---

    _lockScroll() {
        // Prevent body jumping by padding the width of the missing scrollbar
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        if (scrollbarWidth > 0) {
            document.body.style.paddingRight = `${scrollbarWidth}px`;
        }
        document.body.classList.add('overflow-hidden');
    }

    _unlockScroll() {
        document.body.style.paddingRight = '';
        document.body.classList.remove('overflow-hidden');
    }

    _setupAccessibility() {
        document.addEventListener('keydown', this._handleKeydown);
        
        // Find all focusable elements inside the modal
        const focusableString = 'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, [tabindex="0"], [contenteditable]';
        this.focusables = Array.from(this.modal.querySelectorAll(focusableString));
        
        if (this.focusables.length > 0) {
            this.focusables[0].focus();
        } else {
            this.modal.focus();
        }
    }

    _removeAccessibility() {
        document.removeEventListener('keydown', this._handleKeydown);
    }

    _trapFocus(e) {
        if (this.focusables.length === 0) return;

        const firstFocusable = this.focusables[0];
        const lastFocusable = this.focusables[this.focusables.length - 1];

        if (e.shiftKey) { // Shift + Tab
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else { // Tab
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    }
}

/**
 * GLOBAL INITIALIZATION
 * Listens for clicks on any element with data-ldgf-target="#modal-id"
 */
document.addEventListener('DOMContentLoaded', () => {
    // Store instances globally so we don't recreate them on every click
    window.LdgfModalInstances = window.LdgfModalInstances || {};

    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('[data-ldgf-target]');
        if (!trigger) return;

        e.preventDefault();
        const targetSelector = trigger.getAttribute('data-ldgf-target');
        
        let modalInstance = window.LdgfModalInstances[targetSelector];
        
        if (!modalInstance) {
            // Check for custom backdrop option in HTML, e.g., data-ldgf-backdrop="false"
            const backdropOpt = trigger.getAttribute('data-ldgf-backdrop') === 'false' ? false : 'static';
            modalInstance = new LdgfModal(targetSelector, { backdrop: backdropOpt });
            window.LdgfModalInstances[targetSelector] = modalInstance;
        }

        modalInstance.open(trigger);
    });
});
